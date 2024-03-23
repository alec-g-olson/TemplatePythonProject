from pathlib import Path

import pytest

from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.project_structure import get_docs_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_dict,
)


@pytest.fixture(scope="module")
def docs_dir(real_project_root_dir: Path) -> Path:
    return get_docs_dir(project_root=real_project_root_dir)


def test_subprojects_documented(real_project_root_dir: Path, docs_dir: Path) -> None:
    subprojects_doc_file = docs_dir.joinpath("subprojects.rst")
    subproject_name_to_doc_link = {
        context.value: [f":doc:`{context.value}`"]
        for context in SubprojectContext
        if context
        not in [
            SubprojectContext.PYPI,
            SubprojectContext.DOCUMENTATION_ENFORCEMENT,
            SubprojectContext.ALL,
        ]
    }
    subproject_name_to_doc_link[SubprojectContext.PYPI.value] = [
        f":doc:`{get_project_name(project_root=real_project_root_dir)}`"
    ]
    subproject_name_to_doc_link[SubprojectContext.DOCUMENTATION_ENFORCEMENT.value] = []
    observed_header_to_doc_links = {}
    current_header = None
    last_line = None
    for line in subprojects_doc_file.read_text().splitlines():
        line = line.strip()
        if line and all(char == "-" for char in line):
            current_header = last_line.lower().replace(" ", "_")
            observed_header_to_doc_links[current_header] = []
        if line.startswith(":doc:`"):
            observed_header_to_doc_links[current_header].append(line)
        last_line = line
    assert observed_header_to_doc_links == subproject_name_to_doc_link


def test_subproject_code_docs_exists_for_subprojects_with_code(
    real_project_root_dir: Path, docs_dir: Path
) -> None:
    subprojects_code_doc_file = docs_dir.joinpath("subproject_code_docs.rst")
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    expected_subprojects_with_code_docs = {
        context.value
        for context, subproject in subprojects.items()
        if subproject.get_src_dir().exists()
    }
    expected_subprojects_with_code_docs.remove(SubprojectContext.PYPI.value)
    expected_subprojects_with_code_docs.add(
        get_project_name(project_root=real_project_root_dir)
    )
    expected_subprojects_with_code_docs = sorted(expected_subprojects_with_code_docs)
    subprojects_with_code_docs = []
    record_lines = False
    for line in subprojects_code_doc_file.read_text().splitlines():
        line = line.strip()
        if record_lines and line:
            subprojects_with_code_docs.append(line)
        if line == ":maxdepth: 1":
            record_lines = True
    assert sorted(subprojects_with_code_docs) == expected_subprojects_with_code_docs
