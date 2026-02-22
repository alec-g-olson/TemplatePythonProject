from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest
from test_utils.command_runner import run_command_and_save_logs

from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)


@pytest.mark.usefixtures("mock_new_branch", "ticket_for_current_branch")
def test_check_feature_test_added(
    mock_project_root: Path,
    current_ticket_id: str,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
    request: SubRequest,
) -> None:
    build_support_subproject = get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    )
    project_name = get_project_name(project_root=mock_project_root)
    build_support_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
    ).joinpath(f"test_{current_ticket_id}_{project_name}.py").write_text(
        "def test_something() -> None:\n    assert True\n"
    )
    return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "check_process"],
        cwd=mock_project_root,
        test_name=request.node.name,
        real_project_root_dir=real_project_root_dir,
    )
    assert return_code == 0


@pytest.mark.usefixtures("mock_new_branch")
def test_fail_check_feature_test_not_added_to_branch(
    mock_project_root: Path,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
    request: SubRequest,
) -> None:
    return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "check_process"],
        cwd=mock_project_root,
        test_name=request.node.name,
        real_project_root_dir=real_project_root_dir,
    )
    assert return_code != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_pass_check_feature_test_not_added_to_main(
    mock_project_root: Path,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
    request: SubRequest,
) -> None:
    return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "check_process"],
        cwd=mock_project_root,
        test_name=request.node.name,
        real_project_root_dir=real_project_root_dir,
    )
    assert return_code == 0
