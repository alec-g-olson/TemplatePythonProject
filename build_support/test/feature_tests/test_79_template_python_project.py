import pytest
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)
from test_utils.command_runner import FeatureTestCommandContext, run_command


@pytest.mark.usefixtures("mock_new_branch", "ticket_for_current_branch")
def test_check_feature_test_added(
    command_context: FeatureTestCommandContext, current_ticket_id: str
) -> None:
    build_support_subproject = get_python_subproject(
        project_root=command_context.mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    )
    project_name = get_project_name(project_root=command_context.mock_project_root)
    build_support_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
    ).joinpath(f"test_{current_ticket_id}_{project_name}.py").write_text(
        "def test_something() -> None:\n    assert True\n"
    )
    return_code, _, _ = run_command(command_context, ["check_process"])
    assert return_code == 0


@pytest.mark.usefixtures("mock_new_branch")
def test_fail_check_feature_test_not_added_to_branch(
    command_context: FeatureTestCommandContext,
) -> None:
    return_code, _, _ = run_command(
        command_context, ["check_process"], expect_failure=True
    )
    assert return_code != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_pass_check_feature_test_not_added_to_main(
    command_context: FeatureTestCommandContext,
) -> None:
    return_code, _, _ = run_command(command_context, ["check_process"])
    assert return_code == 0
