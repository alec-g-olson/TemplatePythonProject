import re
from http import HTTPStatus
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import requests
from pydantic import BaseModel

# Anything that isn't a square closing bracket
hyperlink_display_name = "[^]]+"
# Anything that isn't a closing paren
hyperlink_dest = "[^)]+"

HYPERLINK_PATTERN = r"\[({0})]\(\s*({1})\s*\)".format(
    hyperlink_display_name, hyperlink_dest
)


@pytest.fixture()
def project_readme(real_project_root_dir: Path) -> Path:
    return real_project_root_dir.joinpath("README.md")


def _build_header_regex(header_level: int, header_title: str) -> str:
    return "^" + "#" * header_level + " " + header_title + "$"


def _build_header_regexes(header_level_dict: Dict[str, int]) -> List[str]:
    return [
        _build_header_regex(level, title) for title, level in header_level_dict.items()
    ]


class ReadmeHeaderInfo(BaseModel):
    readme_path: Path
    header: str


class BadHyperlinkInfo(BaseModel):
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
            readme_path=readme_path.relative_to(readme_path.parent),
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
            striped_line = line.rstrip()
            if striped_line.startswith("#"):
                current_header = None
            for regex_str in header_regexes:
                if not headers_with_details_found[regex_str] and re.match(
                    regex_str, striped_line
                ):
                    current_header = regex_str
                    break
            if (
                striped_line
                and current_header
                and not re.match(current_header, striped_line)
            ):
                headers_with_details_found[current_header] = True

    return [
        ReadmeHeaderInfo(
            readme_path=readme_path.relative_to(readme_path.parent),
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
            if line.startswith("#"):
                expected_header = False
                for regex_str in header_regexes:
                    if re.match(regex_str, line):
                        expected_header = True
                        break
                if not expected_header:
                    extra_headers.append(
                        ReadmeHeaderInfo(
                            readme_path=readme_path.relative_to(readme_path.parent),
                            header=line,
                        )
                    )
    return extra_headers


def _is_broken_hyperlink(
    current_dir: Path,
    hyperlink: Tuple[str, str],
    check_weblinks: bool,
    all_headers: List[str],
) -> bool:
    if hyperlink[1].startswith("http"):
        if (
            check_weblinks
        ):  # pragma: no cover - might not hit if check_weblinks is false
            return requests.get(hyperlink[1]).status_code != HTTPStatus.OK
        return False  # pragma: no cover - might not hit if check_weblinks is true
    if hyperlink[1].startswith("#"):
        return hyperlink[1] not in all_headers
    return not current_dir.joinpath(hyperlink[1]).exists()


def _get_all_bad_hyperlinks(
    readme_path: Path, check_weblinks: bool
) -> List[
    BadHyperlinkInfo
]:  # pragma: no cover - has branches not reached if all tests pass
    bad_hyperlinks = []
    if readme_path.exists():
        all_headers = [line for line in readme_path.open() if line.startswith("#")]
        possible_header_links = []
        for header in all_headers:
            start_of_header = 0
            for char in header:
                if char in ["#", " "]:
                    start_of_header += 1
                else:
                    break
            strip_header = "#" + header[start_of_header:-1]
            strip_header = strip_header.replace(" ", "-").lower()
            possible_header_links.append(strip_header)
        bad_hyperlinks = [
            BadHyperlinkInfo(
                readme_path=readme_path.relative_to(readme_path.parent),
                line_number=line_number,
                hyperlink=str(hyperlink),
            )
            for line_number, line in enumerate(readme_path.open(), 1)
            for hyperlink in re.findall(HYPERLINK_PATTERN, line)
            if _is_broken_hyperlink(
                current_dir=readme_path.parent,
                hyperlink=hyperlink,
                check_weblinks=check_weblinks,
                all_headers=possible_header_links,
            )
        ]
    return bad_hyperlinks


TOP_LEVEL_README_HEADER_LEVEL_DICT = {
    "Template Project": 1,
    "Goals of Template Project": 3,
    "Enforcement of Development Practices": 4,
    "Enforcement of Development and Production Environments": 4,
    "Organization of Template Project": 3,
    "Scope of Template Project": 3,
    "Architecture Layers": 4,
    "Environments this Template Strives to Support": 4,
    "Additional Control this Template Tries to Provide": 4,
    "Creating a New Project From This Template": 3,
    "Primary Services": 2,
    "API": 3,
    "Other Service": 3,
    "Getting Started": 1,
    "Development Environment Setup": 2,
    "PyCharm": 3,
    "PyCharm: Setting the Python Interpreter": 4,
    "PyCharm: Setting Src and Test Folders": 4,
    "PyCharm: Configuring PyCharm to Use Pytest": 4,
    "PyCharm: Adjusting Docstring Settings": 4,
    "PyCharm: Setting Vertical Ruler to 88": 4,
    "PyCharm: Checking Your Work by Running the Tests": 4,
    "VS Code": 3,
    "Working in this Repository": 1,
    "Selected Build Commands": 2,
    "Tools Enforcing Dev Standards": 2,
    "Poetry": 3,
    "PyTest and PyTest-Cov": 3,
    "Ruff": 3,
    "Process and Style Enforcement": 3,
    "MyPy": 3,
    "Bandit": 3,
    "Technologies and Frameworks": 1,
    "Major Technologies": 2,
    "Other tools": 2,
    "Versioning": 1,
    "Creating a Release": 1,
}

TOP_LEVEL_README_HEADER_REGEXES = _build_header_regexes(
    header_level_dict=TOP_LEVEL_README_HEADER_LEVEL_DICT
)


def test_top_level_readme_has_required_headers(project_readme: Path) -> None:
    missing_headers = _get_missing_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=project_readme,
    )
    assert missing_headers == []


def test_top_level_header_have_details(project_readme: Path) -> None:
    headers_missing_details = _get_headers_missing_details(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=project_readme,
    )
    assert headers_missing_details == []


def test_top_level_readme_has_no_extra_headers(project_readme: Path) -> None:
    extra_headers = _get_extra_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES,
        readme_path=project_readme,
    )
    assert extra_headers == []


def test_top_level_readme_hyperlinks_are_valid(
    project_readme: Path, check_weblinks: bool
) -> None:
    assert (
        _get_all_bad_hyperlinks(
            readme_path=project_readme, check_weblinks=check_weblinks
        )
        == []
    )
