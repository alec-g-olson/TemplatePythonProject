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
        if not isinstance(self.name, str):
            raise ValueError(
                '"name" in project settings must have a string value, '
                f"found type {self.name.__class__.__name__}."
            )
        if not isinstance(self.license, str):
            raise ValueError(
                '"license" in project settings must have a string value, '
                f"found type {self.license.__class__.__name__}."
            )
        if not isinstance(self.organization, str):
            raise ValueError(
                '"organization" in project settings must have a string value, '
                f"found type {self.license.__class__.__name__}."
            )
        licenses_with_templates = get_licenses_with_templates()
        if self.license.lower() not in licenses_with_templates:
            raise ValueError(
                'Once cast to a lower case string, "license" must be '
                "one of:\n  "
                + "  \n".join(sorted(licenses_with_templates))
                + f"found {self.license.lower()} instead."
            )
