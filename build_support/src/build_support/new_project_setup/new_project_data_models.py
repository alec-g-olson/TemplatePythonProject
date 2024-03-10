"""A data model for managing new project settings.

This module exists to conceptually isolate the serialization and
deserialization of new_project_settings.yaml.
"""

from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated
from yaml import safe_dump, safe_load

from build_support.new_project_setup.license_templates import (
    get_licenses_with_templates,
    is_valid_license_template,
)


def validate_license(template_key: str) -> str:
    """Validates that the supplied license value has a template.

    Args:
        template_key (str): The name of a license template.

    Returns:
        str: The provided `template_key` if it is valid.

    Raises:
        ValueError: If the `template_key` is invalid.
    """
    template_key = template_key.lower()
    if not is_valid_license_template(template_key=template_key):
        raise ValueError(
            'Once cast to a lower case string, "license" must be '
            "one of:\n  "
            + "  \n".join(sorted(get_licenses_with_templates()))
            + f"found {template_key} instead.",
        )
    return template_key


class Organization(BaseModel):
    """An object containing the information about an organization."""

    name: str
    contact_email: str

    def formatted_name_and_email(self) -> str:
        """Builds a label for the organization name and contact email.

        Returns:
            str: A formatted string with the name and contact info of the org.
        """
        return f"{self.name} <{self.contact_email}>"


class ProjectSettings(BaseModel):
    """An object containing the project settings for this project."""

    name: str
    license: Annotated[str, AfterValidator(validate_license)]
    organization: Organization

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ProjectSettings":
        """Builds an object from a YAML str.

        Args:
            yaml_str (str): String of the YAML representation of a ProjectSettings
                instance.

        Returns:
            GitInfo: A ProjectSettings object parsed from the YAML.
        """
        return ProjectSettings.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str.

        Returns:
            str: A YAML representation of this ProjectSettings instance.
        """
        return safe_dump(self.model_dump())
