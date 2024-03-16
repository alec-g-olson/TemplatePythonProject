from pathlib import Path

import pytest

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
)


def test_get_python_subproject(mock_project_root: Path) -> None:
    for context in SubprojectContext:
        if context != SubprojectContext.ALL:
            assert get_python_subproject(
                subproject_context=context, project_root=mock_project_root
            ) == PythonSubproject(
                project_root=mock_project_root, subproject_name=context.value
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
            project_root=mock_project_root, subproject_name=subproject_context.value
        )
        for subproject_context in SubprojectContext
        if subproject_context != SubprojectContext.ALL
    }
