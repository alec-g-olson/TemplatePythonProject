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


class TestFileInfo(BaseModel):
    """A dataclass for organizing source file information."""

    file_path: Path
    tests_passed: datetime | None

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
    def validate_file_path(cls, value: Any) -> Any:  # noqa: ANN401
        if isinstance(value, str):
            return Path(value)
        return value


class FileCacheInfo(BaseModel):
    """An object containing the cache information for a file."""

    subproject_context: SubprojectContext
    test_cache_info: list[TestFileInfo] = Field(default=[])

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

    def most_recent_conftest_update(self, test_dir: Path) -> datetime:
        top_level_test_dir = self.subproject.get_test_dir()
        current_test = test_dir
        most_recent_update = datetime.min.replace(tzinfo=UTC)
        while current_test != top_level_test_dir:
            current_conftest = current_test.joinpath(CONFTEST_NAME)
            if current_conftest.exists():
                conftest_updated = self.get_last_modified_time(
                    file_path=current_conftest
                )
                if conftest_updated > most_recent_update:
                    most_recent_update = conftest_updated
            current_test = current_test.parent
        top_conftest = top_level_test_dir.joinpath(CONFTEST_NAME)
        if top_conftest.exists():
            conftest_updated = self.get_last_modified_time(file_path=top_conftest)
            most_recent_update = max(conftest_updated, most_recent_update)
        return most_recent_update

    def most_recent_src_file_update(self) -> datetime:
        return max(
            (
                self.get_last_modified_time(file_path=src_file)
                for src_file, _ in self.subproject.get_src_unit_test_file_pairs()
            ),
            default=datetime.min.replace(tzinfo=UTC),
        )

    def get_test_info_for_file(self, file_path: Path) -> TestFileInfo:
        file_info = next(
            (
                info
                for info in self.cache_data.test_cache_info
                if info.file_path == file_path
            ),
            None,
        )
        if file_info is None:
            file_info = TestFileInfo(file_path=file_path, tests_passed=None)
            self.cache_data.test_cache_info.append(file_info)
        return file_info

    @staticmethod
    def get_last_modified_time(file_path: Path) -> datetime:
        """Gets the ISO 8601 timestamp that the file was last modified.

        Args:
            file_path (Path): The path to the file.

        Returns:
            str: The ISO 8601 timestamp that the file was last modified.
        """
        return datetime.fromtimestamp(timestamp=file_path.stat().st_mtime, tz=UTC)

    def update_test_pass_timestamp(self, file_path: Path) -> None:
        """Records when a test passed using the current timestamp.

        Args:
            file_path (Path): The path to the test file.

        Returns:
            None
        """
        test_file_cache_info = self.get_test_info_for_file(file_path=file_path)
        current_time = datetime.now(tz=UTC)
        test_file_cache_info.tests_passed = current_time
