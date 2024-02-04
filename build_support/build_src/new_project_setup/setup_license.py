"""Module exists to conceptually organize all work that involves license templates."""

import json
from copy import copy
from datetime import datetime
from functools import cache
from pathlib import Path

import requests

GIT_HUB_TEMPLATE_URL = "https://api.github.com/licenses"
ALL_RIGHTS_RESERVED_KEY = "all-rights-reserved"

ALL_RIGHTS_RESERVED_TEMPLATE = (
    "All Rights Reserved\n"
    "\n"
    "Copyright (c) [year] [fullname]\n"
    "\n"
    'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
    "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
    "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
    "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
    "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n"
    "THE SOFTWARE.\n"
)


@cache
def _get_github_license_template_info_blobs() -> list[dict[str, str]]:
    """Gets all the info for GitHub license templates."""
    return json.loads(requests.get(url=GIT_HUB_TEMPLATE_URL, timeout=30).text)


@cache
def get_licenses_with_templates() -> list[str]:
    """Gets a list of licenses with templates."""
    supported_github_license_data = _get_github_license_template_info_blobs()
    supported_github_licenses = [blob["key"] for blob in supported_github_license_data]
    return supported_github_licenses + [ALL_RIGHTS_RESERVED_KEY]


@cache
def get_template_for_license(template_key: str) -> str:
    """Gets the template for a license."""
    template_key_lower = template_key.lower()
    licenses_with_templates = get_licenses_with_templates()
    if template_key_lower not in licenses_with_templates:
        raise ValueError(
            '"template_key" must be one of:\n  '
            + "  \n".join(sorted(licenses_with_templates))
            + f"found {template_key_lower} instead."
        )
    if template_key_lower == ALL_RIGHTS_RESERVED_KEY:
        return ALL_RIGHTS_RESERVED_TEMPLATE
    else:
        supported_github_license_data = _get_github_license_template_info_blobs()
        blob_by_key = {blob["key"]: blob for blob in supported_github_license_data}
        template_info = blob_by_key[template_key_lower]
        template = json.loads(requests.get(url=template_info["url"], timeout=30).text)
        return template["body"]


def get_new_license_content(template_key: str, organization: str) -> str:
    """Gets the content of a new license file using the template specified."""
    working_license_content = copy(get_template_for_license(template_key=template_key))
    current_year = str(datetime.now().year)
    working_license_content = working_license_content.replace("[year]", current_year)
    working_license_content = working_license_content.replace(
        "[fullname]", organization
    )
    return working_license_content


def write_new_license_from_template(
    license_file_path: Path, template_key: str, organization: str
) -> None:
    """Writes a new license to the file specified."""
    license_content = get_new_license_content(
        template_key=template_key, organization=organization
    )
    license_file_path.write_text(license_content)
