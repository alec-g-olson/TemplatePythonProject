import json
from copy import copy
from pathlib import Path
from unittest.mock import patch

import pytest
import responses

from build_support.ci_cd_vars.file_and_dir_path_vars import get_license_templates_dir
from build_support.new_project_setup.license_templates import (
    ALL_RIGHTS_RESERVED_KEY,
    ALL_RIGHTS_RESERVED_TEMPLATE,
    GIT_HUB_TEMPLATE_URL,
    REAL_LICENSE_TEMPLATE_DIR,
    REAL_PROJECT_ROOT,
    get_github_license_template_info_blobs,
    get_licenses_with_templates,
    get_template_for_license,
    is_valid_license_template,
)


def test_constants_not_changed_by_accident() -> None:
    assert copy(GIT_HUB_TEMPLATE_URL) == "https://api.github.com/licenses"
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
    assert copy(REAL_PROJECT_ROOT) == Path(__file__).parent.parent.parent.parent.parent
    assert copy(REAL_LICENSE_TEMPLATE_DIR) == get_license_templates_dir(
        project_root=REAL_PROJECT_ROOT
    )


def test_get_licenses_with_templates() -> None:
    licenses_with_templates = get_licenses_with_templates()
    assert ALL_RIGHTS_RESERVED_KEY in licenses_with_templates
    assert len(licenses_with_templates) > 1


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


#######################################################################################
# To avoid rate limiting we are caching any call made to GitHub as a file.  The
# following tests ensure good coverage of caching code.  Do not modify constants or
# mock requests outside of these tests.
#######################################################################################


@responses.activate
def test_get_github_license_template_info_blobs(mock_project_root: Path) -> None:
    license_template_info_blobs = get_license_templates_dir(
        project_root=mock_project_root
    ).joinpath("license_template_info_blobs.json")
    json_data = [{"someKey": "someVal"}]
    get_response = responses.get(url=GIT_HUB_TEMPLATE_URL, json=json_data)
    with patch(
        "build_support.new_project_setup.license_templates.REAL_LICENSE_TEMPLATE_DIR",
        get_license_templates_dir(project_root=mock_project_root),
    ):
        assert not license_template_info_blobs.exists()
        assert get_response.call_count == 0
        assert get_github_license_template_info_blobs() == json_data
        assert get_response.call_count == 1
        assert license_template_info_blobs.exists()
        assert json.loads(license_template_info_blobs.read_text()) == json_data
        assert get_github_license_template_info_blobs() == json_data
        assert get_response.call_count == 1


@responses.activate
def test_get_template_for_license(mock_project_root: Path) -> None:
    fake_license_name = "some-fake-license"
    license_template_file = get_license_templates_dir(
        project_root=mock_project_root
    ).joinpath(fake_license_name)
    template_text = "some template text"
    json_data = {"body": template_text}
    template_info_url = f"https://api.github.com/licenses/{fake_license_name}"
    license_template_info_blobs = get_license_templates_dir(
        project_root=mock_project_root
    ).joinpath("license_template_info_blobs.json")
    blob_data = [{"key": fake_license_name, "url": template_info_url}]
    license_template_info_blobs.write_text(json.dumps(blob_data))
    get_response = responses.get(url=template_info_url, json=json_data)
    with patch(
        "build_support.new_project_setup.license_templates.REAL_LICENSE_TEMPLATE_DIR",
        get_license_templates_dir(project_root=mock_project_root),
    ):
        assert not license_template_file.exists()
        assert get_response.call_count == 0
        assert get_template_for_license(template_key=fake_license_name) == template_text
        assert get_response.call_count == 1
        assert license_template_file.exists()
        assert license_template_file.read_text() == template_text
        assert get_template_for_license(template_key=fake_license_name) == template_text
        assert get_response.call_count == 1
