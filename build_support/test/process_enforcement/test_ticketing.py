"""Tests to enforce ticketing discipline."""

from pathlib import Path

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.project_setting_vars import get_project_name


def test_feature_branch_has_matching_ticket_file(
    real_git_info: GitInfo, real_project_root_dir: Path
) -> None:
    """Feature branches must have a matching ticket file.

    The primary branch is exempt from this check.
    """
    branch_name = real_git_info.branch
    project_name = get_project_name(project_root=real_project_root_dir)

    expected_ticket_path = (
        real_project_root_dir / "docs" / "tickets" / project_name / f"{branch_name}.rst"
    )
    primary_branch_name = GitInfo.get_primary_branch_name()
    assert (
        (branch_name != primary_branch_name and expected_ticket_path.exists())
        or branch_name == primary_branch_name  # no requirements for tickets on main
    )
