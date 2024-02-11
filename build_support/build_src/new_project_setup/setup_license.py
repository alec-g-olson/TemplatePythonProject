"""Module exists to make a new license from templates."""

from copy import copy
from datetime import datetime
from pathlib import Path

from new_project_setup.license_templates import get_template_for_license
from new_project_setup.new_project_data_models import Organization

YEAR_TEMPLATE_FIELDS = ["[year]", "[yyyy]"]
COPYRIGHT_OWNER_TEMPLATE_FIELDS = ["[fullname]", "[name of copyright owner]"]


def get_new_license_content(template_key: str, organization: Organization) -> str:
    """Gets the content of a new license file using the template specified."""
    working_license_content = copy(get_template_for_license(template_key=template_key))
    current_year = str(datetime.now().year)
    for year_field in YEAR_TEMPLATE_FIELDS:
        working_license_content = working_license_content.replace(
            year_field, current_year
        )
    for copyright_owner_field in COPYRIGHT_OWNER_TEMPLATE_FIELDS:
        working_license_content = working_license_content.replace(
            copyright_owner_field, organization.formatted_name_and_email()
        )
    return working_license_content


def write_new_license_from_template(
    license_file_path: Path, template_key: str, organization: Organization
) -> None:
    """Writes a new license to the file specified."""
    license_content = get_new_license_content(
        template_key=template_key, organization=organization
    )
    license_file_path.write_text(license_content)
