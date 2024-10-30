import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from build_support.new_project_setup.license_templates import (
    ALL_RIGHTS_RESERVED_KEY,
    get_licenses_with_templates,
    get_template_for_license,
)
from build_support.new_project_setup.new_project_data_models import Organization
from build_support.new_project_setup.setup_license import (
    COPYRIGHT_OWNER_TEMPLATE_FIELDS,
    YEAR_TEMPLATE_FIELDS,
    get_new_license_content,
    write_new_license_from_template,
)


def test_constants_not_changed_by_accident() -> None:
    assert YEAR_TEMPLATE_FIELDS.copy() == ["[year]", "[yyyy]"]
    assert COPYRIGHT_OWNER_TEMPLATE_FIELDS.copy() == [
        "[fullname]",
        "[name of copyright owner]",
    ]


def test_get_new_license_content() -> None:
    expected_license_content = (
        "All Rights Reserved\n"
        "\n"
        "Copyright (c) 2024 Some small group <an.email@gmail.com>\n"
        "\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"  # noqa: E501
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n"
        "THE SOFTWARE.\n"
    )
    with patch(
        "build_support.new_project_setup.setup_license.datetime",
    ) as mock_datetime:
        mock_datetime.now = Mock(
            return_value=datetime(year=2024, month=1, day=28, tzinfo=timezone.utc)
        )
        new_license_content = get_new_license_content(
            template_key=ALL_RIGHTS_RESERVED_KEY,
            organization=Organization.model_validate(
                {"name": "Some small group", "contact_email": "an.email@gmail.com"},
            ),
        )
        assert new_license_content == expected_license_content


@pytest.fixture()
def check_template_compatability(is_on_main: bool) -> bool:
    # We only want to check template compatability if we are
    # on a working branch.  If we are on main and something goes
    # stale it won't be fixable.  Also reduces the number of calls
    # made to the GitHub API during building.
    return not is_on_main


def test_all_templates_supported(check_template_compatability: bool) -> None:
    # won't hit if check_template_compatability is false
    if check_template_compatability:  # pragma: no cov
        known_fields_to_skip = [
            "[This is the first released version of the Lesser GPL.  It also counts\n"
            " as the successor of the GNU Library Public License, version 2, hence\n"
            " the version number 2.1.]",
        ]
        template_field_regex = re.compile(r"\[[^]]+]")
        allowed_fields = (
            YEAR_TEMPLATE_FIELDS
            + COPYRIGHT_OWNER_TEMPLATE_FIELDS
            + known_fields_to_skip
        )
        for template_key in get_licenses_with_templates():
            template_text = get_template_for_license(template_key=template_key)
            fields_to_fill = re.findall(template_field_regex, template_text)
            for field_to_fill in fields_to_fill:
                assert field_to_fill in allowed_fields


def test_write_new_license_from_template(tmp_path: Path) -> None:
    license_dest = tmp_path.joinpath("LICENSE")
    template_key = "mit"
    organization = Organization.model_validate(
        {"name": "Some small group", "contact_email": "an.email@gmail.com"}
    )
    expected_contents = get_new_license_content(
        template_key=template_key,
        organization=organization,
    )
    assert not license_dest.exists()
    write_new_license_from_template(
        license_file_path=license_dest,
        template_key=template_key,
        organization=organization,
    )
    assert license_dest.read_text() == expected_contents
