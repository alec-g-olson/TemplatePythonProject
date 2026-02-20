from pathlib import Path
from subprocess import Popen

import pytest


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
