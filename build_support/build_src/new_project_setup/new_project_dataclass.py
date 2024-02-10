"""A dataclass for managing new project settings.

This module exists to conceptually isolate the serialization and
deserialization of project_settings.yaml.
"""
from new_project_setup.setup_license import (
    get_licenses_with_templates,
    is_valid_license_template,
)
from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated
from yaml import safe_dump, safe_load


def validate_license(template_key: str) -> str:
    """Validates that the supplied license value has a template."""
    template_key = template_key.lower()
    if not is_valid_license_template(template_key=template_key):
        raise ValueError(
            'Once cast to a lower case string, "license" must be '
            "one of:\n  "
            + "  \n".join(sorted(get_licenses_with_templates()))
            + f"found {template_key} instead."
        )
    return template_key


class ProjectSettings(BaseModel):
    """An object containing the project settings for this project."""

    name: str
    license: Annotated[str, AfterValidator(validate_license)]
    organization: str

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ProjectSettings":
        """Builds an object from a json str."""
        return ProjectSettings.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str."""
        return safe_dump(self.model_dump())
