from datetime import datetime
from unittest.mock import MagicMock, patch

from new_project_setup.setup_license import (
    ALL_RIGHTS_RESERVED_KEY,
    ALL_RIGHTS_RESERVED_TEMPLATE,
    GIT_HUB_TEMPLATE_URL,
    get_licenses_with_templates,
    get_new_license_content,
    get_template_for_license,
)


def test_constants_not_changed_by_accident():
    assert GIT_HUB_TEMPLATE_URL == "https://api.github.com/licenses"
    assert ALL_RIGHTS_RESERVED_KEY == "all-rights-reserved"
    assert ALL_RIGHTS_RESERVED_TEMPLATE == (
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


def test_get_licenses_with_templates():
    licenses_with_templates = get_licenses_with_templates()
    assert (
        ALL_RIGHTS_RESERVED_KEY in licenses_with_templates
        and len(licenses_with_templates) > 1
    )


def test_get_template_for_mit():
    assert get_template_for_license(template_key="mit") == (
        "MIT License\n"
        "\n"
        "Copyright (c) [year] [fullname]\n"
        "\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        'of this software and associated documentation files (the "Software"), to deal\n'
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n"
        "\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n"
        "\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"
    )


def test_get_template_for_all_rights_reserved():
    assert (
        get_template_for_license(template_key=ALL_RIGHTS_RESERVED_KEY)
        == ALL_RIGHTS_RESERVED_TEMPLATE
    )


def test_get_new_license_content():
    with patch("new_project_setup.setup_license.datetime") as mock_datetime:
        mock_datetime.now = MagicMock(return_value=datetime(year=2024, month=1, day=28))
        new_license_content = get_new_license_content(
            template_key=ALL_RIGHTS_RESERVED_KEY,
            organization="Some small group <an.email@gmail.com>",
        )
        assert new_license_content == (
            "All Rights Reserved\n"
            "\n"
            "Copyright (c) 2024 Some small group <an.email@gmail.com>\n"
            "\n"
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n"
            "THE SOFTWARE.\n"
        )
