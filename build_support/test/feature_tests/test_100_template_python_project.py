from pathlib import Path
from subprocess import Popen

from git import Head


def test_style_checks_fail_without_ticket_file_for_feature_branch(
    mock_project_root: Path, mock_new_branch: Head, make_command_prefix: list[str]
) -> None:
    branch_name = mock_new_branch.name.split("/")[-1]
    expected_ticket_file = mock_project_root.joinpath(
        "docs", "tickets", f"{branch_name}.rst"
    )
    if expected_ticket_file.exists():
        expected_ticket_file.unlink()

    cmd = Popen(args=[*make_command_prefix, "test_style"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode != 0


def test_style_checks_pass_with_ticket_file_for_feature_branch(
    mock_project_root: Path, mock_new_branch: Head, make_command_prefix: list[str]
) -> None:
    branch_name = mock_new_branch.name.split("/")[-1]
    expected_ticket_file = mock_project_root.joinpath(
        "docs", "tickets", f"{branch_name}.rst"
    )
    expected_ticket_file.write_text(
        "100: Style Ticket Enforcement\n"
        "=============================\n"
        "\n"
        "Overview\n"
        "--------\n"
        "This ticket exists so feature-branch style checks can verify that the\n"
        "required docs/tickets file is present and contains meaningful details.\n"
    )

    cmd = Popen(args=[*make_command_prefix, "test_style"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode == 0
