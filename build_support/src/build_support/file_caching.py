"""The logic for caching the state of files.

This is so we can determine if we need to rerun parts of our validation pipeline.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Tuple

from pydantic import BaseModel, Field, field_serializer
from yaml import safe_dump, safe_load

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)


class FileCacheInfo(BaseModel):
    """An object containing the cache information for a file."""

    subproject_context: SubprojectContext
    cache_info: dict[Path, str] = Field(default={})

    @staticmethod
    def get_file_cache_for(
        subproject_context: SubprojectContext, project_root: Path
    ) -> "FileCacheInfo":
        path_to_file_cache = get_python_subproject(
            subproject_context=subproject_context,
            project_root=project_root,
        ).get_file_cache_yaml()
        if path_to_file_cache.exists():
            return FileCacheInfo.from_yaml(path_to_file_cache.read_text())
        return FileCacheInfo(subproject_context=subproject_context)

    @field_serializer("subproject_context")
    def serialize_subproject_context_as_str(
        self, subproject_context: SubprojectContext
    ) -> str:
        """Args:
            subproject_context:

        Returns:

        """
        return subproject_context.value

    @field_serializer("cache_info")
    def serialize_cache_info_paths_as_str(
        self, cache_info: dict[Path, str]
    ) -> dict[str, str]:
        """Serializes the keys of cache info as strings instead of paths.

        Args:
            cache_info (dict[Path, str]): The cache info.

        Returns:
            str: A version of the cache info using strings as keys instead of paths.
        """
        return {str(path): s for path, s in cache_info.items()}

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


@dataclass
class UnitTestInfo:
    conftest_or_parent_conftest_was_updated: bool
    maybe_conftest_path: Path | None
    src_test_file_pairs: list[Tuple[Path, Path]]


class FileCacheEngine:
    cache_data: FileCacheInfo
    subproject: PythonSubproject

    _CONFTEST_NAME = "conftest.py"

    def __init__(
        self, subproject_context: SubprojectContext, project_root: Path
    ) -> None:
        self.cache_data = FileCacheInfo.get_file_cache_for(
            subproject_context=subproject_context,
            project_root=project_root,
        )
        self.subproject = get_python_subproject(
            subproject_context=subproject_context,
            project_root=project_root,
        )

    def write_text(self) -> None:
        """Returns:

        """
        self.subproject.get_file_cache_yaml().write_text(self.cache_data.to_yaml())

    @staticmethod
    def _is_testable_python_file(path: Path) -> bool:
        """Args:
            path:

        Returns:

        """
        return (
            path.is_file() and path.name.endswith(".py") and path.name != "__init__.py"
        )

    def _recursive_get_unit_test_info(
        self, current_src_folder: Path, parent_conftest_was_updated: bool
    ) -> Iterator[UnitTestInfo]:
        """Yeilds:

        """
        expected_conftest_file = get_corresponding_unit_test_folder_for_src_folder(
            python_pkg_root_dir=self.subproject.get_python_package_dir(),
            unit_test_root_dir=self.subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
            ),
            src_folder_path=current_src_folder,
        ).joinpath(FileCacheEngine._CONFTEST_NAME)
        conftest_updated = False
        maybe_conftest_path = None
        if expected_conftest_file.exists():
            conftest_updated = self.file_has_been_changed(
                file_path=expected_conftest_file
            )
            maybe_conftest_path = expected_conftest_file
        conftest_or_parent_conftest_was_updated = (
            parent_conftest_was_updated or conftest_updated
        )
        paths_in_dir = sorted(current_src_folder.glob("*"))
        src_files = [
            path
            for path in paths_in_dir
            if FileCacheEngine._is_testable_python_file(path=path)
        ]
        dirs = [path for path in paths_in_dir if path.is_dir()]
        if src_files:
            file_pairs = [
                (
                    src_file,
                    get_corresponding_unit_test_folder_for_src_folder(
                        python_pkg_root_dir=self.subproject.get_python_package_dir(),
                        unit_test_root_dir=self.subproject.get_test_suite_dir(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                        src_folder_path=src_file.parent,
                    ).joinpath(f"test_{src_file.name}"),
                )
                for src_file in src_files
            ]
            yield UnitTestInfo(
                conftest_or_parent_conftest_was_updated=conftest_or_parent_conftest_was_updated,
                maybe_conftest_path=maybe_conftest_path,
                src_test_file_pairs=file_pairs,
            )
        for directory in dirs:
            yield from self._recursive_get_unit_test_info(
                current_src_folder=directory,
                parent_conftest_was_updated=conftest_or_parent_conftest_was_updated,
            )

    def get_unit_test_info(self) -> Iterator[UnitTestInfo]:
        """Yields:

        """
        yield from self._recursive_get_unit_test_info(
            current_src_folder=self.subproject.get_python_package_dir(),
            parent_conftest_was_updated=False,
        )

    def file_has_been_changed(self, file_path: Path) -> bool:
        """Checks if a file has been changed since the last time it was cached.

        Args:
            file_path (Path): The path to the file being checked.

        Returns:
            bool: True if the file has been changed or was not in cache, otherwise
                false.

        Raises:
            ValueError: If the file provided is not in the `group_root_dir`.
        """
        abs_file_path = file_path.absolute()
        relative_file_path = abs_file_path.relative_to(self.subproject.get_root_dir())
        last_modified = datetime.fromtimestamp(
            timestamp=abs_file_path.stat().st_mtime, tz=timezone.utc
        ).isoformat()
        has_been_changed = True
        if (
            relative_file_path in self.cache_data.cache_info
            and last_modified == self.cache_data.cache_info[relative_file_path]
        ):
            has_been_changed = False
        self.cache_data.cache_info[relative_file_path] = last_modified
        return has_been_changed


def get_corresponding_unit_test_folder_for_src_folder(
    python_pkg_root_dir: Path, unit_test_root_dir: Path, src_folder_path: Path
) -> Path:
    """Args:
        python_pkg_root_dir:
        unit_test_root_dir:
        src_folder_path:

    Returns:

    """
    relative_path = src_folder_path.relative_to(python_pkg_root_dir)
    return unit_test_root_dir.joinpath(relative_path)
