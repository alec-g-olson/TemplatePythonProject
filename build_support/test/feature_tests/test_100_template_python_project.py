import copy
from pathlib import Path

import pytest
from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from git import Repo
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


@pytest.mark.usefixtures("mock_new_branch", "dummy_feature_test")
def test_process_checks_fail_without_ticket_file_for_feature_branch(
    default_command_context: FeatureTestCommandContext, current_ticket_file: Path
) -> None:
    if current_ticket_file.exists():
        current_ticket_file.unlink()

    failure_context = copy.copy(default_command_context)
    failure_context.expect_failure = True
    return_code, _, _ = run_command_and_save_logs(failure_context, ["check_process"])
    assert return_code != 0


@pytest.mark.usefixtures(
    "mock_new_branch", "dummy_feature_test", "ticket_for_current_branch"
)
def test_process_checks_pass_with_ticket_file_for_feature_branch(
    default_command_context: FeatureTestCommandContext,
) -> None:
    return_code, _, _ = run_command_and_save_logs(
        default_command_context, ["check_process"]
    )
    assert return_code == 0


def test_process_checks_pass_on_main_branch_without_ticket_file(
    default_command_context: FeatureTestCommandContext, mock_lightweight_project: Repo
) -> None:
    primary_branch_name = GitInfo.get_primary_branch_name()
    mock_lightweight_project.git.checkout(primary_branch_name)
    project_name = get_project_name(
        project_root=default_command_context.real_project_root_dir
    )
    main_ticket_path = default_command_context.mock_project_root.joinpath(
        "docs", "tickets", project_name, f"{primary_branch_name}.rst"
    )
    if main_ticket_path.exists():
        main_ticket_path.unlink()

    return_code, _, _ = run_command_and_save_logs(
        default_command_context, ["check_process"]
    )
    assert return_code == 0


def test_process_checks_pass_on_main_branch_with_ticket_file(
    default_command_context: FeatureTestCommandContext, mock_lightweight_project: Repo
) -> None:
    primary_branch_name = GitInfo.get_primary_branch_name()
    mock_lightweight_project.git.checkout(primary_branch_name)
    project_name = get_project_name(
        project_root=default_command_context.real_project_root_dir
    )
    main_ticket_path = default_command_context.mock_project_root.joinpath(
        "docs", "tickets", project_name, f"{primary_branch_name}.rst"
    )
    main_ticket_path.parent.mkdir(parents=True, exist_ok=True)
    main_ticket_path.write_text("Main Ticket\n===========\n")

    return_code, _, _ = run_command_and_save_logs(
        default_command_context, ["check_process"]
    )
    assert return_code == 0
