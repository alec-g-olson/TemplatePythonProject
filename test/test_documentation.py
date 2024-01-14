import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import requests
from conftest import PROJECT_ROOT_DIR

README_FILENAME = "README.md"

TOP_LEVEL_README_PATH = PROJECT_ROOT_DIR.joinpath(README_FILENAME)

# Anything that isn't a square closing bracket
hyperlink_display_name = "[^]]+"
# Anything that isn't a closing paren
hyperlink_dest = "[^)]+"

HYPERLINK_PATTERN = r"\[({0})]\(\s*({1})\s*\)".format(
    hyperlink_display_name, hyperlink_dest
)


@pytest.fixture
def check_weblinks(is_on_main):
    return not is_on_main


def _build_header_regex(header_level: int, header_title: str) -> str:
    return "^" + "#" * header_level + " " + header_title + "$"


def _build_header_regexes(header_level_dict: Dict[str, int]) -> List[str]:
    return [
        regex_str
        for regex_str in [
            _build_header_regex(level, title)
            for title, level in header_level_dict.items()
        ]
    ]


@dataclass
class ReadmeHeaderInfo:
    readme_path: Path
    header: str


@dataclass
class BadHyperlinkInfo:
    readme_path: Path
    line_number: int
    hyperlink: str


def _get_missing_headers(
    header_regexes: List[str], readme_path: Path
) -> List[
    ReadmeHeaderInfo
]:  # pragma: no cover - has branches not reached if all tests pass
    headers_found = {regex: False for regex in header_regexes}
    if readme_path.exists():
        for line in readme_path.open():
            for regex_str in header_regexes:
                if not headers_found[regex_str] and re.match(regex_str, line):
                    headers_found[regex_str] = True
                    break
    return [
        ReadmeHeaderInfo(
            readme_path=readme_path.relative_to(PROJECT_ROOT_DIR),
            header=regex_str[1:-1].replace("\\", ""),
        )
        for regex_str in headers_found
        if not headers_found[regex_str]
    ]


def _get_headers_missing_details(
    header_regexes: List[str], readme_path: Path
) -> List[
    ReadmeHeaderInfo
]:  # pragma: no cover - has branches not reached if all tests pass
    headers_with_details_found = {regex: False for regex in header_regexes}
    current_header = None
    if readme_path.exists():
        for line in readme_path.open():
            line = line.rstrip()
            if line.startswith("#"):
                current_header = None
            for regex_str in header_regexes:
                if not headers_with_details_found[regex_str] and re.match(
                    regex_str, line
                ):
                    current_header = regex_str
                    break
            if line and current_header and not re.match(current_header, line):
                headers_with_details_found[current_header] = True

    return [
        ReadmeHeaderInfo(
            readme_path=readme_path.relative_to(PROJECT_ROOT_DIR),
            header=regex_str[1:-1].replace("\\", ""),
        )
        for regex_str in headers_with_details_found
        if not headers_with_details_found[regex_str]
    ]


def _get_extra_headers(
    header_regexes: List[str], readme_path: Path
) -> List[
    ReadmeHeaderInfo
]:  # pragma: no cover - has branches not reached if all tests pass
    extra_headers = []
    if readme_path.exists():
        for line in readme_path.open():
            if re.match(r"^#", line):
                expected_header = False
                for regex_str in header_regexes:
                    if re.match(regex_str, line):
                        expected_header = True
                        break
                if not expected_header:
                    extra_headers.append(
                        ReadmeHeaderInfo(
                            readme_path=readme_path.relative_to(PROJECT_ROOT_DIR),
                            header=line,
                        )
                    )
    return extra_headers


def _is_broken_hyperlink(
    current_dir: Path, hyperlink: Tuple[str, str], check_weblinks: bool
) -> bool:
    if hyperlink[1].startswith("http"):
        if (
            check_weblinks
        ):  # pragma: no cover - might not hit if check_weblinks is false
            return requests.get(hyperlink[1]).status_code != 200
        else:
            return False  # pragma: no cover - might not hit if check_weblinks is true
    else:  # pragma: no cover - only checked if README.md references a local file
        return not current_dir.joinpath(hyperlink[1]).exists()


def _get_all_bad_hyperlinks(
    readme_path: Path, check_weblinks: bool
) -> List[
    BadHyperlinkInfo
]:  # pragma: no cover - has branches not reached if all tests pass
    bad_hyperlinks = []
    line_number = 1
    if readme_path.exists():
        for line in readme_path.open():
            hyperlinks = re.findall(HYPERLINK_PATTERN, line)
            for hyperlink in hyperlinks:
                if _is_broken_hyperlink(
                    current_dir=readme_path.parent,
                    hyperlink=hyperlink,
                    check_weblinks=check_weblinks,
                ):
                    bad_hyperlinks.append(
                        BadHyperlinkInfo(
                            readme_path=readme_path.relative_to(PROJECT_ROOT_DIR),
                            line_number=line_number,
                            hyperlink=str(hyperlink),
                        )
                    )
            line_number += 1
    return bad_hyperlinks


TOP_LEVEL_README_HEADER_LEVEL_DICT = {
    "Template Project": 1,
    "Primary Services": 2,
    "API": 3,
    "Other Service": 3,
    "Getting Started": 1,
    "Development Environment Setup": 2,
    "Setting the Python Interpreter": 3,
    "Setting Src and Test Folders": 3,
    "Configuring PyCharm to Use Pytest": 3,
    "Checking Your Work by Running the Tests in PyCharm": 3,
    "Working in this Repository": 2,
    "Selected Build Commands": 3,
    "Technologies and Frameworks": 2,
    "Major Technologies": 3,
    "Other tools": 3,
    "Versioning": 1,
    "Creating a Release": 1,
}

TOP_LEVEL_README_HEADER_REGEXES = _build_header_regexes(
    header_level_dict=TOP_LEVEL_README_HEADER_LEVEL_DICT
)


def test_top_level_readme_has_required_headers():
    missing_headers = _get_missing_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=TOP_LEVEL_README_PATH,
    )
    assert missing_headers == []


def test_top_level_header_have_details():
    headers_missing_details = _get_headers_missing_details(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=TOP_LEVEL_README_PATH,
    )
    assert headers_missing_details == []


def test_top_level_readme_has_no_extra_headers():
    extra_headers = _get_extra_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=TOP_LEVEL_README_PATH,
    )
    assert extra_headers == []


def test_top_level_readme_hyperlinks_are_valid(check_weblinks):
    assert (
        _get_all_bad_hyperlinks(
            readme_path=TOP_LEVEL_README_PATH, check_weblinks=check_weblinks
        )
        == []
    )
