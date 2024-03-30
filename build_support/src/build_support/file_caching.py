"""The logic for caching the state of files.

This is so we can determine if we need to rerun parts of our validation pipeline.
"""

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, field_serializer
from yaml import safe_dump, safe_load


class FileCacheInfo(BaseModel):
    """An object containing the cache information for a file."""

    group_root_dir: Path
    cache_info: dict[Path, str]

    @field_serializer("group_root_dir")
    def serialize_group_root_dir_path_as_str(self, group_root_dir: Path) -> str:
        """Serializes the group root dir as a string instead of as a path.

        Args:
            group_root_dir (Path): The group root dir.

        Returns:
            str: A string representation of the group root dir path obj.
        """
        return str(group_root_dir)

    @field_serializer("cache_info")
    def serialize_cache_info_path_as_str(
        self, cache_info: dict[Path, str]
    ) -> dict[str, str]:
        """Serializes the keys of cache info as strings instead of paths.

        Args:
            cache_info (dict[Path, str]): The cache info.

        Returns:
            str: A version of the cache info using strings as keys instead of paths.
        """
        return {str(path): s for path, s in cache_info.items()}

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
        relative_file_path = abs_file_path.relative_to(self.group_root_dir)
        last_modified = datetime.fromtimestamp(
            timestamp=abs_file_path.stat().st_mtime, tz=timezone.utc
        ).isoformat()
        has_been_changed = True
        if (
            relative_file_path in self.cache_info
            and last_modified == self.cache_info[relative_file_path]
        ):
            has_been_changed = False
        self.cache_info[relative_file_path] = last_modified
        return has_been_changed

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
