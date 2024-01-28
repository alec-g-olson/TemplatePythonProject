"""A dataclass for managing new project settings.

This module exists to conceptually isolate the serialization and
deserialization of project_settings.yaml.
"""
from dataclasses import dataclass

from new_project_setup.setup_license import get_licenses_with_templates
from yaml import safe_dump, safe_load


@dataclass
class ProjectSettings:
    """An object containing the project settings for this project."""

    name: str
    license: str
    organization: str

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ProjectSettings":
        """Builds an object from a json str."""
        yaml_vals = safe_load(yaml_str)
        project_settings = ProjectSettings(**yaml_vals)
        project_settings._validate_settings()
        return project_settings

    def to_yaml(self) -> str:
        """Dumps object as a yaml str."""
        return safe_dump(self.__dict__)

    def _validate_settings(self):
        """Validates the values in this instance of ProjectSettings."""
        assert isinstance(self.name, str)
        assert isinstance(self.license, str)
        assert self.license.lower() in get_licenses_with_templates()
