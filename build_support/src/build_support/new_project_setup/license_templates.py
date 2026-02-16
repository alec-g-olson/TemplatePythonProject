"""Module for handling licence template information.

License templates are stored as committed resource files in the
``license_templates_resources/`` directory adjacent to this module.
Each file is named after its license key (e.g. ``mit``, ``gpl-3.0``)
and contains the full template body text.

Attributes:
    | ALL_RIGHTS_RESERVED_KEY: The value we use to indicate we want to use an all
        rights reserved license template.
    | ALL_RIGHTS_RESERVED_TEMPLATE: A string containing an all rights reserved
        template.
    | LICENSE_TEMPLATES_DIR: A path to the committed resource directory containing
        license template files.
"""

from pathlib import Path

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

LICENSE_TEMPLATES_DIR = Path(__file__).parent / "license_templates"


def get_licenses_with_templates() -> list[str]:
    """Gets a list of licenses with templates.

    Returns:
        list[str]: A list of all valid template names.
    """
    licenses_with_templates = [ALL_RIGHTS_RESERVED_KEY]
    licenses_with_templates.extend(
        sorted(f.name for f in LICENSE_TEMPLATES_DIR.iterdir() if f.is_file())
    )
    return licenses_with_templates


def is_valid_license_template(template_key: str) -> bool:
    """Checks to see if the template_key is valid.

    Args:
        template_key (str): The name of a license template.

    Returns:
        bool: Is there a template for the provided template_key.
    """
    template_key_lower = template_key.lower()
    licenses_with_templates = get_licenses_with_templates()
    return template_key_lower in licenses_with_templates


def get_template_for_license(template_key: str) -> str:
    """Gets the template for a license.

    Args:
        template_key (str): The name of a license template.

    Returns:
          str: The license template for the key provided.
    """
    template_key_lower = template_key.lower()
    if not is_valid_license_template(template_key=template_key):
        msg = (
            '"template_key" must be one of:\n  '
            + "  \n".join(sorted(get_licenses_with_templates()))
            + f"found {template_key_lower} instead."
        )
        raise ValueError(msg)
    if template_key_lower == ALL_RIGHTS_RESERVED_KEY:
        return ALL_RIGHTS_RESERVED_TEMPLATE
    license_template_file = LICENSE_TEMPLATES_DIR / template_key_lower
    return license_template_file.read_text()
