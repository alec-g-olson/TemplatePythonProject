"""The logic for caching the state of files.

This module provides functionality to track file changes and determine which tests need
to be run.
It implements the following requirements:
1. Unit tests should be run if:
   - The source file has been updated since the test last passed
   - The test file has been updated since it last passed
   - Any conftest files the test relies on have been updated

2. Feature tests should be run if:
   - Any source files in the subproject have been updated
   - Any conftest files the feature test relies on have been updated

Attributes:
    | FEATURE_TEST_FILE_NAME_REGEX: The regex we use to find files with feature tests.

"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field, field_serializer, field_validator
from yaml import safe_dump, safe_load

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)

CONFTEST_NAME = "conftest.py"


class CacheInfoSuite(StrEnum):
    """An Enum to track the type of cache info being tracked."""

    SRC_FILE = "SRC_FILE"
    CONFTEST = "CONFTEST"
    UNIT_TEST = "UNIT_TEST"
    FEATURE_TEST = "FEATURE_TEST"


TEST_CACHES = [CacheInfoSuite.UNIT_TEST, CacheInfoSuite.FEATURE_TEST]


class BasicFileInfo(BaseModel):
    """A dataclass for organizing source file information."""

    file_path: Path
    updated: datetime

    @field_serializer("file_path")
    def serialize_file_path(self, file_path: Path) -> str:
        """Serialize file_path as a string.

        Args:
            file_path (Path): The file path to serialize.

        Returns:
            str: The serialized file path as a string.
        """
        return str(file_path)

    @field_validator("file_path", mode="before")
    @classmethod
    def validate_file_path(cls, value: Any) -> Any:
        if isinstance(value, str):
            return Path(value)
        return value


class TestFileInfo(BasicFileInfo):
    """A dataclass for organizing test file information."""

    tests_passed: datetime | None


class FileCacheInfo(BaseModel):
    """An object containing the cache information for a file."""

    subproject_context: SubprojectContext
    src_file_cache_info: list[BasicFileInfo] = Field(default=[])
    conftest_cache_info: list[BasicFileInfo] = Field(default=[])
    unit_test_cache_info: list[TestFileInfo] = Field(default=[])
    feature_test_cache_info: list[TestFileInfo] = Field(default=[])

    @staticmethod
    def get_file_cache_for(
        subproject_context: SubprojectContext, project_root: Path
    ) -> "FileCacheInfo":
        """Gets the file cache for a subproject.

        Args:
            subproject_context (SubprojectContext): The subproject to get a file cache
                for.
            project_root (Path): The path to the root of the project.

        Returns:
            FileCacheInfo:  An object holding the information about when files were last
                updated.
        """
        path_to_file_cache = get_python_subproject(
            subproject_context=subproject_context, project_root=project_root
        ).get_file_cache_yaml()
        if path_to_file_cache.exists():
            return FileCacheInfo.from_yaml(path_to_file_cache.read_text())
        return FileCacheInfo(subproject_context=subproject_context)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "FileCacheInfo":
        """Builds an object from a YAML str.

        Args:
            yaml_str (str): String of the YAML representation of a ProjectSettings
                instance.

        Returns:
            GitInfo: A ProjectSettings object parsed from the YAML.
        """
        return FileCacheInfo.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str.

        Returns:
            str: A YAML representation of this ProjectSettings instance.
        """
        return safe_dump(self.model_dump(mode="json"))


class NotATestSuiteError(ValueError):
    """Error raised when a CacheInfoSuite is not a test suite."""

    def __init__(self, cache_info_suite: CacheInfoSuite) -> None:
        """Initialize the error with a message about the invalid CacheInfoSuite.

        Args:
            cache_info_suite (CacheInfoSuite): The CacheInfoSuite that is not a test
                file suite.
        """
        super().__init__(f"{cache_info_suite} is not a test suite.")


@dataclass
class UnitTestInfo:
    """A dataclass for organizing unit test information."""

    src_file_path: Path
    test_file_path: Path


@dataclass
class FeatureTestInfo:
    test_file_path: Path


FEATURE_TEST_FILE_NAME_REGEX = re.compile(r"test_.+_.+\.py")


class FileCacheEngine:
    """A class for managing file cache information."""

    cache_data: FileCacheInfo
    subproject: PythonSubproject

    def __init__(
        self, subproject_context: SubprojectContext, project_root: Path
    ) -> None:
        """Init method for FileCacheEngine.

        Args:
            subproject_context (SubprojectContext): The subproject this object will
                manage the file cache for.
            project_root (Path): The path to the root of the project.

        Returns:
            None
        """
        self.cache_data = FileCacheInfo.get_file_cache_for(
            subproject_context=subproject_context, project_root=project_root
        )
        self.subproject = get_python_subproject(
            subproject_context=subproject_context, project_root=project_root
        )

    def write_text(self) -> None:
        """Writes the cache data to the subproject's file cache yaml.

        Returns:
            None
        """
        self.subproject.get_file_cache_yaml().write_text(self.cache_data.to_yaml())

    @staticmethod
    def _is_testable_python_file(path: Path) -> bool:
        """A method for checking if a file is testable.

        Args:
            path (Path): Path to the file that will be checked to see if it is testable.

        Returns:
            bool: Is the file testable?
        """
        return (
            path.is_file() and path.name.endswith(".py") and path.name != "__init__.py"
        )

    def _most_recent_conftest_update(self, test_dir: Path) -> datetime:
        top_level_test_dir = self.subproject.get_test_dir()
        current_test = test_dir
        most_recent_update = datetime.min
        while current_test != top_level_test_dir:
            current_conftest = current_test.joinpath(CONFTEST_NAME)
            if current_conftest.exists():
                conftest_updated = self._get_basic_info_for_file(
                    cache_info_suite=CacheInfoSuite.CONFTEST, file_path=current_conftest
                ).updated
                if conftest_updated > most_recent_update:
                    most_recent_update = conftest_updated
            current_test = current_test.parent
        top_conftest = top_level_test_dir.joinpath(CONFTEST_NAME)
        if top_conftest.exists():
            conftest_updated = self._get_basic_info_for_file(
                cache_info_suite=CacheInfoSuite.CONFTEST, file_path=top_conftest
            ).updated
            if conftest_updated > most_recent_update:
                most_recent_update = conftest_updated
        return most_recent_update

    def _recursive_get_unit_test_info(
        self, current_src_folder: Path
    ) -> Iterator[UnitTestInfo]:
        """An inner method to recursively get the unit test information.

        Args:
            current_src_folder (Path): Path to the src folder being traversed.

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for test caching.
        """
        current_unit_test_dir = get_corresponding_unit_test_folder_for_src_folder(
            python_pkg_root_dir=self.subproject.get_python_package_dir(),
            unit_test_root_dir=self.subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
            ),
            src_folder_path=current_src_folder,
        ).joinpath(CONFTEST_NAME)
        most_recent_conftest_update = self._most_recent_conftest_update(
            test_dir=current_unit_test_dir
        )
        paths_in_dir = sorted(current_src_folder.glob("*"))
        src_files = [
            path
            for path in paths_in_dir
            if FileCacheEngine._is_testable_python_file(path=path)
        ]
        dirs = [path for path in paths_in_dir if path.is_dir()]
        if src_files:
            for src_file in src_files:
                test_file = get_corresponding_unit_test_folder_for_src_folder(
                    python_pkg_root_dir=self.subproject.get_python_package_dir(),
                    unit_test_root_dir=self.subproject.get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                    ),
                    src_folder_path=src_file.parent,
                ).joinpath(f"test_{src_file.name}")
                if test_file.exists():
                    src_file_info = self._get_basic_info_for_file(
                        cache_info_suite=CacheInfoSuite.SRC_FILE, file_path=src_file
                    )
                    test_file_info = self._get_test_info_for_file(
                        test_cache_info_suite=CacheInfoSuite.UNIT_TEST,
                        file_path=test_file,
                    )
                    if (
                        test_file_info.tests_passed is None
                        or test_file_info.tests_passed < src_file_info.updated
                        or test_file_info.tests_passed < test_file_info.updated
                        or test_file_info.tests_passed < most_recent_conftest_update
                    ):
                        yield UnitTestInfo(
                            src_file_path=src_file, test_file_path=test_file
                        )
                else:
                    msg = f"Expected {test_file} to exist!"
                    raise ValueError(msg)

        for directory in dirs:
            yield from self._recursive_get_unit_test_info(current_src_folder=directory)

    def get_unit_tests_to_run(self) -> Iterator[UnitTestInfo]:
        """Gets information required to run unit tests.

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for test caching.
        """
        yield from self._recursive_get_unit_test_info(
            current_src_folder=self.subproject.get_python_package_dir()
        )

    def _get_cache_info_for_suite(
        self, cache_info_suite: CacheInfoSuite
    ) -> list[BasicFileInfo]:
        """Gets the cache info for the appropriate suite.

        Args:
            cache_info_suite: The suite of cache info requested.

        Returns:
            dict[Path, str]: The cache info for the suite requested.
        """
        if cache_info_suite == CacheInfoSuite.SRC_FILE:
            return self.cache_data.src_file_cache_info
        if cache_info_suite == CacheInfoSuite.CONFTEST:
            return self.cache_data.conftest_cache_info
        if cache_info_suite == CacheInfoSuite.UNIT_TEST:
            return self.cache_data.unit_test_cache_info
        if cache_info_suite == CacheInfoSuite.FEATURE_TEST:
            return self.cache_data.feature_test_cache_info
        # will only hit if enum not covered
        msg = f"{cache_info_suite.__name__} is not a supported type."  # pragma: no cov
        raise ValueError(msg)  # pragma: no cov

    def _get_cache_info_for_test_suite(
        self, test_cache_info_suite: CacheInfoSuite
    ) -> list[TestFileInfo]:
        if test_cache_info_suite not in TEST_CACHES:
            raise NotATestSuiteError(test_cache_info_suite)
        if test_cache_info_suite == CacheInfoSuite.UNIT_TEST:
            return self.cache_data.unit_test_cache_info
        if test_cache_info_suite == CacheInfoSuite.FEATURE_TEST:
            return self.cache_data.feature_test_cache_info
        # will only hit if enum not covered
        msg = (  # pragma: no cov
            f"{test_cache_info_suite} is not a supported type."
        )
        raise ValueError(msg)  # pragma: no cov

    def _initialize_file_info(
        self, cache_info_suite: CacheInfoSuite, file_path: Path
    ) -> BasicFileInfo:
        file_updated = FileCacheEngine._get_last_modified_time(file_path=file_path)
        if cache_info_suite in TEST_CACHES:
            test_file_info = TestFileInfo(
                file_path=file_path, updated=file_updated, tests_passed=None
            )
            test_cache_info = self._get_cache_info_for_test_suite(
                test_cache_info_suite=cache_info_suite
            )
            test_cache_info.append(test_file_info)
            return test_file_info
        file_info = BasicFileInfo(file_path=file_path, updated=file_updated)
        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        cache_info.append(file_info)
        return file_info

    def _info_exists_for_file(
        self, cache_info_suite: CacheInfoSuite, file_path: Path
    ) -> bool:
        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        existing_info = next(
            (info for info in cache_info if info.file_path == file_path), None
        )
        return existing_info is not None

    def _get_basic_info_for_file(
        self, cache_info_suite: CacheInfoSuite, file_path: Path
    ) -> BasicFileInfo:
        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        file_info = next(
            (info for info in cache_info if info.file_path == file_path), None
        )
        if file_info is None:
            file_info = self._initialize_file_info(
                cache_info_suite=cache_info_suite, file_path=file_path
            )
        return file_info

    def _get_test_info_for_file(
        self, test_cache_info_suite: CacheInfoSuite, file_path: Path
    ) -> TestFileInfo:
        if test_cache_info_suite not in TEST_CACHES:
            raise NotATestSuiteError(test_cache_info_suite)
        basic_file_info = self._get_basic_info_for_file(
            cache_info_suite=test_cache_info_suite, file_path=file_path
        )
        return cast(TestFileInfo, basic_file_info)

    @staticmethod
    def _get_last_modified_time(file_path: Path) -> datetime:
        """Gets the ISO 8601 timestamp that the file was last modified.

        Args:
            file_path (Path): The path to the file.

        Returns:
            str: The ISO 8601 timestamp that the file was last modified.
        """
        return datetime.fromtimestamp(timestamp=file_path.stat().st_mtime, tz=UTC)

    def _file_has_been_changed_since_last_timestamp_update(
        self, file_path: Path, cache_info_suite: CacheInfoSuite
    ) -> bool:
        """Checks if a file has been changed since the last time it was cached.

        Args:
            file_path (Path): The path to the file being checked.
            cache_info_suite (CacheInfoSuite): The suite of relevant cache info.

        Returns:
            bool: True if the file has been changed or was not in cache, otherwise
                false.

        Raises:
            ValueError: If the file provided is not in the `group_root_dir`.
        """
        if not self._info_exists_for_file(
            cache_info_suite=cache_info_suite, file_path=file_path
        ):
            return True
        file_cache_info = self._get_basic_info_for_file(
            cache_info_suite=cache_info_suite, file_path=file_path
        )
        last_modified = FileCacheEngine._get_last_modified_time(file_path=file_path)
        return last_modified > file_cache_info.updated

    def update_file_timestamp(
        self, file_path: Path, cache_info_suite: CacheInfoSuite
    ) -> None:
        """Updates the file modification timestamp in the cache.

        Args:
            file_path (Path): The path to the file.
            cache_info_suite (CacheInfoSuite): The suite of relevant cache info.

        Returns:
            None
        """
        file_cache_info = self._get_basic_info_for_file(
            cache_info_suite=cache_info_suite, file_path=file_path
        )
        last_modified = FileCacheEngine._get_last_modified_time(file_path=file_path)
        file_cache_info.updated = last_modified

    def update_test_pass_timestamp(
        self, file_path: Path, cache_info_suite: CacheInfoSuite
    ) -> None:
        """Records when a test passed using the current timestamp.

        Args:
            file_path (Path): The path to the test file.
            cache_info_suite (CacheInfoSuite): The suite of relevant cache info.
                Should be UNIT_TEST_PASS or FEATURE_TEST_PASS.

        Returns:
            None
        """
        test_file_cache_info = self._get_test_info_for_file(
            test_cache_info_suite=cache_info_suite, file_path=file_path
        )
        current_time = datetime.now(tz=UTC)
        test_file_cache_info.tests_passed = current_time

    def _recursive_get_src_folders(self, current_src_folder: Path) -> Iterator[Path]:
        """An inner method to recursively get the all src files.

        Args:
            current_src_folder (Path): Path to the src folder being traversed.

        Yields:
            Iterator[UnitTestInfo]: Generator of src files for test caching.
        """
        paths_in_dir = sorted(current_src_folder.glob("*"))
        src_files = [
            path
            for path in paths_in_dir
            if FileCacheEngine._is_testable_python_file(path=path)
        ]
        dirs = [path for path in paths_in_dir if path.is_dir()]
        if src_files:
            yield from src_files
        for directory in dirs:
            yield from self._recursive_get_src_folders(current_src_folder=directory)

    def get_feature_tests_to_run(self) -> Iterator[FeatureTestInfo]:
        """Gets information required to run feature tests.

        Returns:
            FeatureTestInfo: A dataclass with the cache information for feature tests.
        """
        feature_test_dir = self.subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        )
        most_recent_conftest_update = self._most_recent_conftest_update(
            test_dir=feature_test_dir
        )
        most_recent_src_file_update = max(
            (
                self._get_basic_info_for_file(
                    cache_info_suite=CacheInfoSuite.SRC_FILE, file_path=src_file
                ).updated
                for src_file in self._recursive_get_src_folders(
                    current_src_folder=self.subproject.get_python_package_dir()
                )
            )
        )

        test_files = [
            file
            for file in feature_test_dir.glob("*")
            if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
        ]

        # Update feature test file timestamps
        for test_file in test_files:
            test_file_info = self._get_test_info_for_file(
                test_cache_info_suite=CacheInfoSuite.FEATURE_TEST, file_path=test_file
            )
            if (
                test_file_info.tests_passed is not None
                and test_file_info.tests_passed < most_recent_conftest_update
                and test_file_info.tests_passed < most_recent_src_file_update
            ):
                yield FeatureTestInfo(test_file_path=test_file)


def get_corresponding_unit_test_folder_for_src_folder(
    python_pkg_root_dir: Path, unit_test_root_dir: Path, src_folder_path: Path
) -> Path:
    """Get the unit test folder corresponding to a src folder.

    Args:
        python_pkg_root_dir (Path): Path to the python package root.
        unit_test_root_dir (Path): Path to the subproject's unit test folder.
        src_folder_path (Path): Path to the src folder.

    Returns:
        Path: Path to a unit test folder corresponding to a src folder.
    """
    relative_path = src_folder_path.relative_to(python_pkg_root_dir)
    return unit_test_root_dir.joinpath(relative_path)
