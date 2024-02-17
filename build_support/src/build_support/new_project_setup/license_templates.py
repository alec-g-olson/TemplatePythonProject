"""Module for handling licence template information."""
import json
from pathlib import Path
from time import sleep

import requests
from build_support.ci_cd_vars.file_and_dir_path_vars import get_license_templates_dir

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


#######################################################################################
# To avoid rate limiting we are caching any call made to GitHub as a file.  The
# "@cache" decorator is not as clean as a solution as it would initially appear,
# because each test calls it again in a new context.  To ensure that we don't call
# out to GitHub during each test, we have "hard coded" the real project root so that
# all test calls use the same folder.
#######################################################################################
REAL_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
REAL_LICENSE_TEMPLATE_DIR = get_license_templates_dir(project_root=REAL_PROJECT_ROOT)


def get_github_license_template_info_blobs() -> list[dict[str, str]]:
    """Gets all the info for GitHub license templates."""
    license_template_info_blobs = REAL_LICENSE_TEMPLATE_DIR.joinpath(
        "license_template_info_blobs.json"
    )
    if license_template_info_blobs.exists():
        template_info_blobs = json.loads(license_template_info_blobs.read_text())
    else:
        sleep(0.1)  # avoid rate limiting
        template_info_blobs = json.loads(
            requests.get(url=GIT_HUB_TEMPLATE_URL, timeout=30).text
        )
        license_template_info_blobs.write_text(
            json.dumps(template_info_blobs, indent=2)
        )
    return template_info_blobs


def get_licenses_with_templates() -> list[str]:
    """Gets a list of licenses with templates."""
    supported_github_license_data = get_github_license_template_info_blobs()
    supported_github_licenses = [blob["key"] for blob in supported_github_license_data]
    return supported_github_licenses + [ALL_RIGHTS_RESERVED_KEY]


def is_valid_license_template(template_key: str) -> bool:
    """Checks to see if the template_key is valid."""
    template_key_lower = template_key.lower()
    licenses_with_templates = get_licenses_with_templates()
    return template_key_lower in licenses_with_templates


def get_template_for_license(template_key: str) -> str:
    """Gets the template for a license."""
    template_key_lower = template_key.lower()
    if not is_valid_license_template(template_key=template_key):
        raise ValueError(
            '"template_key" must be one of:\n  '
            + "  \n".join(sorted(get_licenses_with_templates()))
            + f"found {template_key_lower} instead."
        )
    if template_key_lower == ALL_RIGHTS_RESERVED_KEY:
        return ALL_RIGHTS_RESERVED_TEMPLATE
    else:
        license_template_file = REAL_LICENSE_TEMPLATE_DIR.joinpath(template_key_lower)
        if license_template_file.exists():
            template = license_template_file.read_text()
        else:
            supported_github_license_data = get_github_license_template_info_blobs()
            blob_by_key = {blob["key"]: blob for blob in supported_github_license_data}
            template_info = blob_by_key[template_key_lower]
            sleep(0.1)  # avoid rate limiting
            template = json.loads(
                requests.get(url=template_info["url"], timeout=30).text
            )["body"]
            license_template_file.write_text(template)
        return template
