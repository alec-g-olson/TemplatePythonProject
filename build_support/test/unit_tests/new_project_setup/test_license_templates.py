from copy import copy
from pathlib import Path

import pytest

from build_support.new_project_setup.license_templates import (
    ALL_RIGHTS_RESERVED_KEY,
    ALL_RIGHTS_RESERVED_TEMPLATE,
    LICENSE_TEMPLATES_DIR,
    get_licenses_with_templates,
    get_template_for_license,
    is_valid_license_template,
)


def test_constants_not_changed_by_accident() -> None:
    assert copy(ALL_RIGHTS_RESERVED_KEY) == "all-rights-reserved"
    assert copy(ALL_RIGHTS_RESERVED_TEMPLATE) == (
        "All Rights Reserved\n"
        "\n"
        "Copyright (c) [year] [fullname]\n"
        "\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"  # noqa: E501
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n"
        "THE SOFTWARE.\n"
    )
    assert copy(LICENSE_TEMPLATES_DIR) == (
        Path(__file__).parent.parent.parent.parent
        / "src"
        / "build_support"
        / "new_project_setup"
        / "license_templates"
    )


def test_license_templates_dir_exists() -> None:
    assert LICENSE_TEMPLATES_DIR.is_dir()
    template_files = [f for f in LICENSE_TEMPLATES_DIR.iterdir() if f.is_file()]
    assert len(template_files) > 0


def test_get_licenses_with_templates() -> None:
    licenses_with_templates = get_licenses_with_templates()
    assert ALL_RIGHTS_RESERVED_KEY in licenses_with_templates
    assert len(licenses_with_templates) > 1


def test_get_licenses_with_templates_includes_all_resource_files() -> None:
    licenses = get_licenses_with_templates()
    resource_files = sorted(
        f.name for f in LICENSE_TEMPLATES_DIR.iterdir() if f.is_file()
    )
    for resource_file in resource_files:
        assert resource_file in licenses


def test_get_template_for_mit() -> None:
    assert get_template_for_license(template_key="mit") == (
        "MIT License\n"
        "\n"
        "Copyright (c) [year] [fullname]\n"
        "\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        'of this software and associated documentation files (the "Software"), to deal\n'  # noqa: E501
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n"
        "\n"
        "The above copyright notice and this permission notice shall be included in all\n"  # noqa: E501
        "copies or substantial portions of the Software.\n"
        "\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"  # noqa: E501
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"  # noqa: E501
        "SOFTWARE.\n"
    )


def test_get_template_for_all_rights_reserved() -> None:
    assert (
        get_template_for_license(template_key=ALL_RIGHTS_RESERVED_KEY)
        == ALL_RIGHTS_RESERVED_TEMPLATE
    )


def test_get_template_bad_value() -> None:
    bad_key = "WHOOP_WHOOP_DIDDY_WHOOP_WHOOP"
    expected_message = (
        '"template_key" must be one of:\n  '
        + "  \n".join(sorted(get_licenses_with_templates()))
        + f"found {bad_key.lower()} instead."
    )
    with pytest.raises(ValueError, match=expected_message):
        get_template_for_license(template_key=bad_key)


@pytest.mark.parametrize(
    ("template_key", "is_valid"),
    [
        (ALL_RIGHTS_RESERVED_KEY.lower(), True),
        (ALL_RIGHTS_RESERVED_KEY.upper(), True),
        ("MIT", True),
        ("Mit", True),
        ("mit", True),
        ("mit license", False),
        ("WHOOP_WHOOP_DIDDY_WHOOP_WHOOP", False),
    ],
)
def test_is_valid_license_template(template_key: str, is_valid: bool) -> None:
    assert is_valid_license_template(template_key=template_key) == is_valid


def test_all_resource_files_are_readable() -> None:
    for template_file in LICENSE_TEMPLATES_DIR.iterdir():
        assert template_file.is_file(), f"{template_file.name} is not a regular file"
        content = template_file.read_text()
        assert len(content) > 0, f"Template {template_file.name} is empty"
