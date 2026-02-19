import re
from http import HTTPStatus
from pathlib import Path

import pytest
import requests
from pydantic import BaseModel

# Anything that isn't a square closing bracket
hyperlink_display_name = "[^]]+"
# Anything that isn't a closing paren
hyperlink_dest = "[^)]+"

HYPERLINK_PATTERN = rf"\[({hyperlink_display_name})]\(\s*({hyperlink_dest})\s*\)"


@pytest.fixture
def project_readme(real_project_root_dir: Path) -> Path:
    return real_project_root_dir.joinpath("README.md")


@pytest.fixture
def agents_markdown(real_project_root_dir: Path) -> Path:
    return real_project_root_dir.joinpath("AGENTS.md")


@pytest.fixture
def claude_markdown(real_project_root_dir: Path) -> Path:
    return real_project_root_dir.joinpath("CLAUDE.md")


def _build_header_regex(header_level: int, header_title: str) -> str:
    return "^" + "#" * header_level + " " + header_title + "$"


def _build_header_regexes(header_level_dict: dict[str, int]) -> list[str]:
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
    header_regexes: list[str], readme_path: Path
) -> list[
    ReadmeHeaderInfo
]:  # pragma: no cov - has branches not reached if all tests pass
    headers_found = dict.fromkeys(header_regexes, False)
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
    header_regexes: list[str], readme_path: Path
) -> list[
    ReadmeHeaderInfo
]:  # pragma: no cov - has branches not reached if all tests pass
    headers_with_details_found = dict.fromkeys(header_regexes, False)
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
    header_regexes: list[str], readme_path: Path
) -> list[
    ReadmeHeaderInfo
]:  # pragma: no cov - has branches not reached if all tests pass
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
    hyperlink: tuple[str, str],
    check_weblinks: bool,
    all_headers: list[str],
) -> bool:
    if hyperlink[1].startswith("http"):
        if check_weblinks and "gnu.org" not in hyperlink[1]:  # pragma: no cov
            return requests.get(hyperlink[1]).status_code != HTTPStatus.OK
        return False  # pragma: no cov - might not hit if check_weblinks is true
    if hyperlink[1].startswith("#"):
        return hyperlink[1] not in all_headers
    return not current_dir.joinpath(hyperlink[1]).exists()


def _get_all_bad_hyperlinks(
    readme_path: Path, check_weblinks: bool
) -> list[
    BadHyperlinkInfo
]:  # pragma: no cov - has branches not reached if all tests pass
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

AGENTS_HEADER_LEVEL_DICT = {
    "Agent Guide": 1,
    "1. Finding the Ticket for the Current Work": 2,
    "2. Useful Developer Commands": 2,
    "3. Running Commands in Docker": 2,
    "4. Designing Source Code": 2,
    "5. Designing and Writing Tests": 2,
}

AGENTS_HEADER_REGEXES = _build_header_regexes(
    header_level_dict=AGENTS_HEADER_LEVEL_DICT
)


def test_top_level_readme_has_required_headers(project_readme: Path) -> None:
    missing_headers = _get_missing_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES, readme_path=project_readme
    )
    assert missing_headers == []


def test_top_level_header_have_details(project_readme: Path) -> None:
    headers_missing_details = _get_headers_missing_details(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES, readme_path=project_readme
    )
    assert headers_missing_details == []


def test_top_level_readme_has_no_extra_headers(project_readme: Path) -> None:
    extra_headers = _get_extra_headers(
        header_regexes=TOP_LEVEL_README_HEADER_REGEXES, readme_path=project_readme
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


def test_agents_markdown_has_required_headers(agents_markdown: Path) -> None:
    missing_headers = _get_missing_headers(
        header_regexes=AGENTS_HEADER_REGEXES, readme_path=agents_markdown
    )
    assert missing_headers == []


def test_agents_markdown_headers_have_details(agents_markdown: Path) -> None:
    headers_missing_details = _get_headers_missing_details(
        header_regexes=AGENTS_HEADER_REGEXES, readme_path=agents_markdown
    )
    assert headers_missing_details == []


def test_agents_markdown_hyperlinks_are_valid(
    agents_markdown: Path, check_weblinks: bool
) -> None:
    assert (
        _get_all_bad_hyperlinks(
            readme_path=agents_markdown, check_weblinks=check_weblinks
        )
        == []
    )


def test_claude_markdown_has_canonical_agents_link(claude_markdown: Path) -> None:
    non_empty_lines = [
        line.strip() for line in claude_markdown.read_text().splitlines()
    ]
    non_empty_lines = [line for line in non_empty_lines if line]
    assert non_empty_lines == ["See [AGENTS.md](AGENTS.md)."]


def test_claude_markdown_hyperlinks_are_valid(
    claude_markdown: Path, check_weblinks: bool
) -> None:
    assert (
        _get_all_bad_hyperlinks(
            readme_path=claude_markdown, check_weblinks=check_weblinks
        )
        == []
    )
