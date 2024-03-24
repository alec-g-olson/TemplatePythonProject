from pathlib import Path

import pytest

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_all_python_subprojects_with_src,
    get_all_python_subprojects_with_test,
    get_python_subproject,
)


def test_get_python_subproject(mock_project_root: Path) -> None:
    for context in SubprojectContext:
        if context != SubprojectContext.ALL:
            assert get_python_subproject(
                subproject_context=context, project_root=mock_project_root
            ) == PythonSubproject(
                project_root=mock_project_root, subproject_context=context
            )


def test_fail_to_get_python_subproject(mock_project_root: Path) -> None:
    name = SubprojectContext.ALL.name
    msg = f"There is no Python subproject for the {name} subproject."
    with pytest.raises(ValueError, match=msg):
        get_python_subproject(
            subproject_context=SubprojectContext.ALL, project_root=mock_project_root
        )


def test_get_all_python_subprojects_dict(mock_project_root: Path) -> None:
    assert get_all_python_subprojects_dict(project_root=mock_project_root) == {
        subproject_context: PythonSubproject(
            project_root=mock_project_root, subproject_context=subproject_context
        )
        for subproject_context in SubprojectContext
        if subproject_context != SubprojectContext.ALL
    }


def test_get_all_python_subprojects_with_src(mock_project_root: Path) -> None:
    context_to_add_src_for = [SubprojectContext.PYPI, SubprojectContext.BUILD_SUPPORT]
    subproject_dict = get_all_python_subprojects_dict(project_root=mock_project_root)
    for subproject_context in context_to_add_src_for:
        src_dir = subproject_dict[subproject_context].get_src_dir()
        src_dir.mkdir(parents=True, exist_ok=True)
    sorted_contexts = sorted(context_to_add_src_for, key=lambda x: x.name)
    expected_subprojects_with_src = [
        get_python_subproject(
            project_root=mock_project_root, subproject_context=context
        )
        for context in sorted_contexts
    ]
    assert (
        get_all_python_subprojects_with_src(project_root=mock_project_root)
        == expected_subprojects_with_src
    )


def test_get_all_python_subprojects_with_test(mock_project_root: Path) -> None:
    context_to_add_test_for = [
        SubprojectContext.PYPI,
        SubprojectContext.DOCUMENTATION_ENFORCEMENT,
    ]
    subproject_dict = get_all_python_subprojects_dict(project_root=mock_project_root)
    for subproject_context in context_to_add_test_for:
        test_dir = subproject_dict[subproject_context].get_test_dir()
        test_dir.mkdir(parents=True, exist_ok=True)
    sorted_contexts = sorted(context_to_add_test_for, key=lambda x: x.name)
    expected_subprojects_with_test = [
        get_python_subproject(
            project_root=mock_project_root, subproject_context=context
        )
        for context in sorted_contexts
    ]
    assert (
        get_all_python_subprojects_with_test(project_root=mock_project_root)
        == expected_subprojects_with_test
    )
