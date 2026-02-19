from pathlib import Path
from subprocess import Popen

import pytest
from git import Head

from build_support.ci_cd_vars.project_setting_vars import get_project_name


def _get_expected_ticket_file(mock_project_root: Path, branch_name: str) -> Path:
    """Return the ticket path for the branch in the active project folder."""
    project_name = get_project_name(project_root=mock_project_root)
    return mock_project_root.joinpath(
        "docs", "tickets", project_name, f"{branch_name}.rst"
    )


def _write_required_feature_test_for_branch(
    mock_project_root: Path, branch_name: str
) -> None:
    """Create the required feature test file for ``check_process`` to pass."""
    project_name = get_project_name(project_root=mock_project_root)
    ticket_id = branch_name.split("-", maxsplit=1)[0]
    required_feature_test = mock_project_root.joinpath(
        "build_support", "test", "feature_tests", f"test_{ticket_id}_{project_name}.py"
    )
    required_feature_test.write_text("def test_something() -> None:\n    assert True\n")


@pytest.mark.parametrize(
    "feature_branch_fixture_name",
    ["mock_new_branch", "mock_new_branch_without_description"],
)
def test_process_checks_fail_without_ticket_file_for_feature_branch(
    mock_project_root: Path,
    feature_branch_fixture_name: str,
    request: pytest.FixtureRequest,
    make_command_prefix: list[str],
) -> None:
    mock_feature_branch = request.getfixturevalue(feature_branch_fixture_name)
    assert isinstance(mock_feature_branch, Head)
    branch_name = mock_feature_branch.name.split("/")[-1]
    _write_required_feature_test_for_branch(
        mock_project_root=mock_project_root, branch_name=branch_name
    )
    expected_ticket_file = _get_expected_ticket_file(
        mock_project_root=mock_project_root, branch_name=branch_name
    )
    if expected_ticket_file.exists():
        expected_ticket_file.unlink()

    cmd = Popen(args=[*make_command_prefix, "check_process"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode != 0


@pytest.mark.parametrize(
    "feature_branch_fixture_name",
    ["mock_new_branch", "mock_new_branch_without_description"],
)
def test_process_checks_pass_with_ticket_file_for_feature_branch(
    mock_project_root: Path,
    feature_branch_fixture_name: str,
    request: pytest.FixtureRequest,
    make_command_prefix: list[str],
) -> None:
    mock_feature_branch = request.getfixturevalue(feature_branch_fixture_name)
    assert isinstance(mock_feature_branch, Head)
    branch_name = mock_feature_branch.name.split("/")[-1]
    _write_required_feature_test_for_branch(
        mock_project_root=mock_project_root, branch_name=branch_name
    )
    expected_ticket_file = _get_expected_ticket_file(
        mock_project_root=mock_project_root, branch_name=branch_name
    )
    expected_ticket_file.parent.mkdir(parents=True, exist_ok=True)
    expected_ticket_file.write_text(
        "100: Process Ticket Enforcement\n"
        "===============================\n"
        "\n"
        "Overview\n"
        "--------\n"
        "This ticket exists so feature-branch process checks can verify that the\n"
        "required docs/tickets file is present and contains meaningful details.\n"
    )

    cmd = Popen(args=[*make_command_prefix, "check_process"], cwd=mock_project_root)
    cmd.communicate()

    assert cmd.returncode == 0
