"""Module exists to make a new license from templates.

Attributes:
    | YEAR_TEMPLATE_FIELDS: A list of template fields which we should replace
        with the year the new project is made.
    | COPYRIGHT_OWNER_TEMPLATE_FIELDS: A list of template fields which we should
        replace with the owner of the project when the new project is made.
"""

from copy import copy
from datetime import datetime, timezone
from pathlib import Path

from build_support.new_project_setup.license_templates import get_template_for_license
from build_support.new_project_setup.new_project_data_models import Organization

YEAR_TEMPLATE_FIELDS = ["[year]", "[yyyy]"]
COPYRIGHT_OWNER_TEMPLATE_FIELDS = ["[fullname]", "[name of copyright owner]"]


def get_new_license_content(template_key: str, organization: Organization) -> str:
    """Gets the content of a new license file using the template specified.

    Args:
        template_key (str): The name of a license template.
        organization (Organization): Information about the organization to use when
            creating a license from the template.

    Returns:
        str: The contents of a new license using the values from the organization.
    """
    working_license_content = copy(get_template_for_license(template_key=template_key))
    current_year = str(datetime.now(tz=timezone.utc).astimezone().year)
    for year_field in YEAR_TEMPLATE_FIELDS:
        working_license_content = working_license_content.replace(
            year_field,
            current_year,
        )
    for copyright_owner_field in COPYRIGHT_OWNER_TEMPLATE_FIELDS:
        working_license_content = working_license_content.replace(
            copyright_owner_field,
            organization.formatted_name_and_email(),
        )
    return working_license_content


def write_new_license_from_template(
    license_file_path: Path,
    template_key: str,
    organization: Organization,
) -> None:
    """Creates a new license file based on the template_key and organization.

    Args:
        license_file_path (Path): Path to the project's LICENSE file.
        template_key (str): The name of a license template.
        organization (Organization): Information about the organization to use when
            creating a license from the template.

    Returns:
        None
    """
    license_content = get_new_license_content(
        template_key=template_key,
        organization=organization,
    )
    license_file_path.write_text(license_content)
