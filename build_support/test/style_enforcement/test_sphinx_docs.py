import re
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path

import pytest
import requests
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.project_structure import get_docs_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_with_src,
)


@pytest.fixture(scope="module")
def docs_dir(real_project_root_dir: Path) -> Path:
    return get_docs_dir(project_root=real_project_root_dir)


def _makefile_phony_targets(makefile_path: Path) -> set[str]:
    """Extract all .PHONY target names from the root Makefile."""
    text = makefile_path.read_text()
    targets: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(".PHONY:"):
            rest = stripped[7:].strip()  # after ".PHONY:"
            for name in rest.split():
                targets.add(name)
    return targets


def _documented_make_commands(developer_tooling_path: Path) -> set[str]:
    """Extract make target names from the Command column in developer_tooling.rst."""
    text = developer_tooling_path.read_text()
    documented: set[str] = set()
    for match in re.findall(r"^\s+\*\s+-\s+make\s+(\S+)", text, re.MULTILINE):
        documented.add(match)
    return documented


def test_makefile_targets_documented_in_developer_tooling(
    real_project_root_dir: Path, docs_dir: Path
) -> None:
    """Every .PHONY target in the root Makefile must be in developer_tooling.rst."""
    makefile_path = real_project_root_dir.joinpath("Makefile")
    developer_tooling_path = docs_dir.joinpath("developer_tooling.rst")
    makefile_targets = _makefile_phony_targets(makefile_path)
    documented_targets = _documented_make_commands(developer_tooling_path)
    missing = makefile_targets - documented_targets
    assert not missing, (
        f"Makefile target(s) not documented in docs/developer_tooling.rst: "
        f"{sorted(missing)}. Add a row to the Standardized Developer Commands table."
    )


def test_subprojects_documented(real_project_root_dir: Path, docs_dir: Path) -> None:
    subprojects_doc_file = docs_dir.joinpath("subprojects.rst")
    expected_subproject_name_to_doc_link: dict[str, list[str]] = {}
    for context in SubprojectContext:
        subproject_name = (
            context.value
            if context != SubprojectContext.PYPI
            else get_project_name(project_root=real_project_root_dir)
        )
        expected_subproject_name_to_doc_link[context.value] = [
            f":doc:`{subproject_name}`"
        ]
    observed_header_to_doc_links: dict[str, list[str]] = {}
    current_header = None
    last_line = None
    for line in subprojects_doc_file.read_text().splitlines():
        striped_line = line.strip()
        if striped_line and last_line and all(char == "-" for char in striped_line):
            current_header = last_line.lower().replace(" ", "_")
            observed_header_to_doc_links[current_header] = []
        if striped_line and current_header and striped_line.startswith(":doc:`"):
            observed_header_to_doc_links[current_header].append(striped_line)
        last_line = striped_line
    assert observed_header_to_doc_links == expected_subproject_name_to_doc_link


def test_subproject_code_docs_exists_for_subprojects_with_code(
    real_project_root_dir: Path, docs_dir: Path
) -> None:
    subprojects_code_doc_file = docs_dir.joinpath("subproject_code_docs.rst")
    expected_subprojects_with_code_docs_set = {
        subproject.subproject_context.value
        for subproject in get_all_python_subprojects_with_src(
            project_root=real_project_root_dir
        )
    }
    expected_subprojects_with_code_docs_set.remove(SubprojectContext.PYPI.value)
    expected_subprojects_with_code_docs_set.add(
        get_project_name(project_root=real_project_root_dir)
    )
    expected_subprojects_with_code_docs = sorted(
        expected_subprojects_with_code_docs_set
    )
    subprojects_with_code_docs = []
    record_lines = False
    for line in subprojects_code_doc_file.read_text().splitlines():
        striped_line = line.strip()
        if record_lines and striped_line:
            subprojects_with_code_docs.append(striped_line)
        if striped_line == ":maxdepth: 1":
            record_lines = True
    assert sorted(subprojects_with_code_docs) == expected_subprojects_with_code_docs


def _is_broken_hyperlink(
    hyperlink: tuple[str, str],
) -> bool:  # pragma: no cov - might not hit if check_weblinks is false
    return (
        hyperlink[1].startswith("http")
        and requests.get(hyperlink[1]).status_code != HTTPStatus.OK
    )


def test_docs_hyperlinks_are_valid(
    real_project_root_dir: Path, check_weblinks: bool
) -> None:
    @dataclass
    class BadHyperlinkInfo:
        name: str
        url: str

    bad_hyperlinks = []

    if check_weblinks:  # pragma: no cov - might not hit if check_weblinks is false
        bad_hyperlinks = [
            BadHyperlinkInfo(name=hyperlink[0], url=hyperlink[1])
            for doc_file in get_docs_dir(project_root=real_project_root_dir).rglob(
                "*.rst"
            )
            for line in doc_file.read_text().splitlines()
            for hyperlink in re.findall(r"`(.+) <(.+)>`_", line)
            if _is_broken_hyperlink(hyperlink=hyperlink)
        ]
    assert bad_hyperlinks == []
