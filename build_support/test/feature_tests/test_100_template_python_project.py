from pathlib import Path
from subprocess import Popen

import pytest
from git import Repo

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.project_setting_vars import get_project_name


@pytest.mark.usefixtures("mock_new_branch", "dummy_feature_test")
def test_process_checks_fail_without_ticket_file_for_feature_branch(
    mock_project_root: Path, current_ticket_file: Path, make_command_prefix: list[str]
) -> None:
    if current_ticket_file.exists():
        current_ticket_file.unlink()

    cmd = Popen(args=[*make_command_prefix, "check_process"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode != 0


@pytest.mark.usefixtures(
    "mock_new_branch", "dummy_feature_test", "ticket_for_current_branch"
)
def test_process_checks_pass_with_ticket_file_for_feature_branch(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    cmd = Popen(args=[*make_command_prefix, "check_process"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode == 0


@pytest.mark.parametrize(
    "main_ticket_exists", [False, True], ids=["no-main-ticket", "main-ticket-exists"]
)
def test_process_checks_pass_on_main_branch_with_or_without_ticket_file(
    mock_project_root: Path,
    mock_lightweight_project: Repo,
    make_command_prefix: list[str],
    main_ticket_exists: bool,
) -> None:
    primary_branch_name = GitInfo.get_primary_branch_name()
    mock_lightweight_project.git.checkout(primary_branch_name)
    project_name = get_project_name(project_root=mock_project_root)
    main_ticket_path = mock_project_root.joinpath(
        "docs", "tickets", project_name, f"{primary_branch_name}.rst"
    )
    if main_ticket_exists:
        main_ticket_path.parent.mkdir(parents=True, exist_ok=True)
        main_ticket_path.write_text("Main Ticket\n===========\n")
    elif main_ticket_path.exists():
        main_ticket_path.unlink()

    cmd = Popen(args=[*make_command_prefix, "check_process"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode == 0
