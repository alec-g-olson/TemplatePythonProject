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
from enum import Enum, StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_serializer
from yaml import safe_dump, safe_load

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)

class BasicFileInfo(BaseModel):
    """A dataclass for organizing source file information."""

    file_path: Path
    updated: datetime

class TestFileInfo(BasicFileInfo):
    """A dataclass for organizing test file information."""

    tests_passed: datetime


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
        return safe_dump(self.model_dump())


class ParentConftestStatus(StrEnum):
    """An enum to track the state of a parent folder's conftest."""

    UPDATED = "updated"
    NOT_UPDATED = "not updated"


@dataclass
class UnitTestInfo:
    """A dataclass for organizing unit test information."""

    src_file_path: Path
    test_file_path: Path


FEATURE_TEST_FILE_NAME_REGEX = re.compile(r"test_.+_.+\.py")


class FileCacheEngine:
    """A class for managing file cache information."""

    cache_data: FileCacheInfo
    subproject: PythonSubproject

    CONFTEST_NAME = "conftest.py"

    class CacheInfoSuite(StrEnum):
        """An Enum to track the type of cache info being tracked."""

        SRC_FILE = "src_file"
        CONFTEST = "conftest"
        UNIT_TEST = "unit_test"
        FEATURE_TEST = "feature_test"

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

    def top_level_conftest_updated(self) -> ParentConftestStatus:
        """Determines if the top level conftest for all test suites was updated.

        Returns:
            ParentConftestStatus: Was the top level conftest for all tests updated?
        """
        top_level_conftest = self.subproject.get_test_dir().joinpath(
            FileCacheEngine.CONFTEST_NAME
        )
        if top_level_conftest.exists():
            self.update_file_timestamp(
                file_path=top_level_conftest,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )
        return (
            ParentConftestStatus.UPDATED
            if top_level_conftest.exists()
            and self.file_has_been_changed_since_last_timestamp_update(
                top_level_conftest,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )
            else ParentConftestStatus.NOT_UPDATED
        )

    def _yield_unit_test_info_if_appropriate(
        self,
        parent_conftest_was_updated: ParentConftestStatus,
        src_file: Path,
        test_file: Path,
    ) -> Iterator[UnitTestInfo]:
        """A method to yield unit test info if appropriate.

        Args:
            parent_conftest_was_updated (ParentConftestStatus): Was the parent conftest
                file updated?
            src_file (Path): The source file to check.
            test_file (Path): The test file to check.

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for test caching.
        """
        src_relative_path = self.get_relative_path_to_subproject(file_path=src_file)
        src_updated = self.cache_data.src_file_cache_info[src_relative_path]
        test_relative_path = self.get_relative_path_to_subproject(file_path=test_file)
        test_passed = self.cache_data.unit_test_pass_info[test_relative_path]
        test_updated = self.cache_data.unit_test_cache_info[test_relative_path]
        if (
            test_passed < src_updated
            or test_passed < test_updated
            or parent_conftest_was_updated == ParentConftestStatus.UPDATED
        ):
            yield UnitTestInfo(src_file_path=src_file, test_file_path=test_file)

    def _recursive_get_unit_test_info(
        self,
        current_src_folder: Path,
        parent_conftest_was_updated: ParentConftestStatus,
    ) -> Iterator[UnitTestInfo]:
        """An inner method to recursively get the unit test information.

        Args:
            current_src_folder (Path): Path to the src folder being traversed.
            parent_conftest_was_updated (ParentConftestStatus): Was the parent conftest
                file updated?

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for test caching.
        """
        expected_conftest_file = get_corresponding_unit_test_folder_for_src_folder(
            python_pkg_root_dir=self.subproject.get_python_package_dir(),
            unit_test_root_dir=self.subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
            ),
            src_folder_path=current_src_folder,
        ).joinpath(FileCacheEngine.CONFTEST_NAME)
        conftest_updated = False
        if expected_conftest_file.exists():
            conftest_updated = self.file_has_been_changed_since_last_timestamp_update(
                file_path=expected_conftest_file,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )
            # Update conftest file timestamp in cache
            self.update_file_timestamp(
                file_path=expected_conftest_file,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )
        conftest_or_parent_conftest_was_updated = (
            ParentConftestStatus.UPDATED
            if parent_conftest_was_updated == ParentConftestStatus.UPDATED
            or conftest_updated
            else ParentConftestStatus.NOT_UPDATED
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
                self.update_file_timestamp(
                    file_path=src_file,
                    cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
                )
                if test_file.exists():
                    self.update_file_timestamp(
                        file_path=test_file,
                        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
                    )
                    self._yield_unit_test_info_if_appropriate(
                        parent_conftest_was_updated=parent_conftest_was_updated,
                        src_file=src_file,
                        test_file=test_file,
                    )
                else:
                    msg = f"Expected {test_file} to exist!"
                    raise ValueError(msg)

        for directory in dirs:
            yield from self._recursive_get_unit_test_info(
                current_src_folder=directory,
                parent_conftest_was_updated=conftest_or_parent_conftest_was_updated,
            )

    def get_unit_tests_to_run(self) -> Iterator[UnitTestInfo]:
        """Gets information required to run unit tests.

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for test caching.
        """
        yield from self._recursive_get_unit_test_info(
            current_src_folder=self.subproject.get_python_package_dir(),
            parent_conftest_was_updated=self.top_level_conftest_updated(),
        )

    def _get_cache_info_for_suite(
        self, cache_info_suite: CacheInfoSuite
    ) -> dict[Path, str]:
        """Gets the cache info for the appropriate suite.

        Args:
            cache_info_suite: The suite of cache info requested.

        Returns:
            dict[Path, str]: The cache info for the suite requested.
        """
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.SRC_FILE:
            return self.cache_data.src_file_cache_info
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.CONFTEST:
            return self.cache_data.conftest_cache_info
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.UNIT_TEST:
            return self.cache_data.unit_test_cache_info
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.UNIT_TEST_SUCCESS:
            return self.cache_data.unit_test_pass_info
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.FEATURE_TEST:
            return self.cache_data.feature_test_cache_info
        if cache_info_suite == FileCacheEngine.CacheInfoSuite.FEATURE_TEST_SUCCESS:
            return self.cache_data.feature_test_pass_info
        # will only hit if enum not covered
        msg = f"{cache_info_suite.__name__} is not a supported type."  # pragma: no cov
        raise ValueError(msg)  # pragma: no cov

    def get_relative_path_to_subproject(self, file_path: Path) -> Path:
        """Gets the relative path for a file to the subproject.

        Args:
            file_path (Path): The path to the file.

        Returns:
            Path: The relative path for the file.
        """
        abs_file_path = file_path.absolute()
        return abs_file_path.relative_to(self.subproject.get_root_dir())

    @staticmethod
    def _get_last_modified_time(file_path: Path) -> str:
        """Gets the ISO 8601 timestamp that the file was last modified.

        Args:
            file_path (Path): The path to the file.

        Returns:
            str: The ISO 8601 timestamp that the file was last modified.
        """
        return datetime.fromtimestamp(
            timestamp=file_path.stat().st_mtime, tz=UTC
        ).isoformat()

    def file_has_been_changed_since_last_timestamp_update(
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
        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        relative_file_path = self.get_relative_path_to_subproject(file_path=file_path)
        last_modified = FileCacheEngine._get_last_modified_time(file_path=file_path)
        return (
            relative_file_path not in cache_info
            or last_modified != cache_info[relative_file_path]
        )

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
        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        relative_file_path = self.get_relative_path_to_subproject(file_path=file_path)
        last_modified = FileCacheEngine._get_last_modified_time(file_path=file_path)
        cache_info[relative_file_path] = last_modified

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
        if cache_info_suite not in (
            FileCacheEngine.CacheInfoSuite.UNIT_TEST_SUCCESS,
            FileCacheEngine.CacheInfoSuite.FEATURE_TEST_SUCCESS,
        ):
            msg = (
                "update_test_pass_timestamp only supports pass cache suites, "
                f"got {cache_info_suite}"
            )
            raise ValueError(msg)

        cache_info = self._get_cache_info_for_suite(cache_info_suite=cache_info_suite)
        relative_file_path = self.get_relative_path_to_subproject(file_path=file_path)
        current_time = datetime.now(tz=UTC).isoformat()
        cache_info[relative_file_path] = current_time

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

    def get_feature_test_info(self) -> FeatureTestInfo:
        """Gets information required to run feature tests.

        Returns:
            FeatureTestInfo: A dataclass with the cache information for feature tests.
        """
        top_level_conftest_updated = self.top_level_conftest_updated()
        feature_test_dir = self.subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        )
        feature_test_conftest = feature_test_dir.joinpath(FileCacheEngine.CONFTEST_NAME)
        feature_test_conftest_updated = (
            feature_test_conftest.exists()
            and self.file_has_been_changed_since_last_timestamp_update(
                feature_test_conftest,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )
        )

        # Update feature test conftest timestamp if it exists
        if feature_test_conftest.exists():
            self.update_file_timestamp(
                file_path=feature_test_conftest,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )

        # Update top-level conftest timestamp if it exists
        top_level_conftest = self.subproject.get_test_dir().joinpath(
            FileCacheEngine.CONFTEST_NAME
        )
        if top_level_conftest.exists():
            self.update_file_timestamp(
                file_path=top_level_conftest,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
            )

        conftest_update_status = (
            ParentConftestStatus.UPDATED
            if top_level_conftest_updated == ParentConftestStatus.UPDATED
            or feature_test_conftest_updated
            else ParentConftestStatus.NOT_UPDATED
        )
        src_files = list(
            self._recursive_get_src_folders(
                current_src_folder=self.subproject.get_python_package_dir()
            )
        )

        # Update source file timestamps
        for src_file in src_files:
            self.update_file_timestamp(
                file_path=src_file,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
            )

        test_files = [
            file
            for file in feature_test_dir.glob("*")
            if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
        ]

        # Update feature test file timestamps
        for test_file in test_files:
            self.update_file_timestamp(
                file_path=test_file,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
            )

        src_files = sorted(src_files)
        test_files = sorted(test_files)
        return FeatureTestInfo(
            conftest_or_parent_conftest_was_updated=conftest_update_status,
            src_files=src_files,
            test_files=test_files,
        )


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
