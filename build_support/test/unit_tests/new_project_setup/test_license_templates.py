import hashlib
from copy import copy
from enum import Enum
from pathlib import Path
from typing import NamedTuple

import pytest

from build_support.new_project_setup.license_templates import (
    ALL_RIGHTS_RESERVED_KEY,
    ALL_RIGHTS_RESERVED_TEMPLATE,
    LICENSE_TEMPLATES_DIR,
    get_licenses_with_templates,
    get_template_for_license,
    is_valid_license_template,
)


class _ResourceChecksum(NamedTuple):
    filename: str
    expected_sha256: str


class KnownLicenseResource(Enum):
    AGPL_3_0 = _ResourceChecksum(
        "agpl-3.0",
        "8486a10c4393cee1c25392769ddd3b2d6c242d6ec7928e1414efff7dfb2f07ef",
    )
    APACHE_2_0 = _ResourceChecksum(
        "apache-2.0",
        "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    )
    BSD_2_CLAUSE = _ResourceChecksum(
        "bsd-2-clause",
        "8116e572e44a918ea5f1b589024fbc673ccddde7a53b3bf95b4eafab0fdcd41e",
    )
    BSD_3_CLAUSE = _ResourceChecksum(
        "bsd-3-clause",
        "f24d1328dbfffe7bf66aa877957db75e60629358357d8c366ccab616fef487ab",
    )
    BSL_1_0 = _ResourceChecksum(
        "bsl-1.0",
        "c9bff75738922193e67fa726fa225535870d2aa1059f91452c411736284ad566",
    )
    CC0_1_0 = _ResourceChecksum(
        "cc0-1.0",
        "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499",
    )
    EPL_2_0 = _ResourceChecksum(
        "epl-2.0",
        "8c349f80764d0648e645f41ef23772a70c995a0924b5235f735f4a3d09df127c",
    )
    GPL_2_0 = _ResourceChecksum(
        "gpl-2.0",
        "8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643",
    )
    GPL_3_0 = _ResourceChecksum(
        "gpl-3.0",
        "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
    )
    LGPL_2_1 = _ResourceChecksum(
        "lgpl-2.1",
        "20c17d8b8c48a600800dfd14f95d5cb9ff47066a9641ddeab48dc54aec96e331",
    )
    MIT = _ResourceChecksum(
        "mit",
        "002c2696d92b5c8cf956c11072baa58eaf9f6ade995c031ea635c6a1ee342ad1",
    )
    MPL_2_0 = _ResourceChecksum(
        "mpl-2.0",
        "3f3d9e0024b1921b067d6f7f88deb4a60cbe7a78e76c64e3f1d7fc3b779b9d04",
    )
    UNLICENSE = _ResourceChecksum(
        "unlicense",
        "6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e",
    )


def _hash_template_file(name: str) -> str:
    text = (LICENSE_TEMPLATES_DIR / name).read_text().replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        / "license_templates_resources"
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


@pytest.mark.parametrize(
    "resource", list(KnownLicenseResource), ids=lambda resource: resource.name
)
def test_license_template_resource_file_matches_expected_checksum(
    resource: KnownLicenseResource,
) -> None:
    assert _hash_template_file(
        resource.value.filename
    ) == resource.value.expected_sha256


def test_license_template_resource_enum_matches_file_count() -> None:
    resource_files = [f for f in LICENSE_TEMPLATES_DIR.iterdir() if f.is_file()]
    assert len(resource_files) == len(KnownLicenseResource)


def test_all_resource_files_are_readable() -> None:
    for template_file in LICENSE_TEMPLATES_DIR.iterdir():
        assert template_file.is_file(), f"{template_file.name} is not a regular file"
        content = template_file.read_text()
        assert len(content) > 0, f"Template {template_file.name} is empty"
