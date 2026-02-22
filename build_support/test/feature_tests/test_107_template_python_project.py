"""Feature tests for branch-scoped Docker image tags."""

from pathlib import Path
from subprocess import run

from git import Head, Repo
from test_utils.command_runner import run_command_and_save_logs

from build_support.ci_cd_vars.git_status_vars import PRIMARY_BRANCH_NAME
from build_support.ci_cd_vars.project_setting_vars import get_project_name


def _expected_image_names(project_root: Path, tag_suffix: str) -> tuple[str, str, str]:
    """Build expected build/dev/prod image names for a tag suffix."""
    project_name = get_project_name(project_root=project_root)
    return (
        f"{project_name}:build{tag_suffix}",
        f"{project_name}:dev{tag_suffix}",
        f"{project_name}:prod{tag_suffix}",
    )


def _assert_expected_images_exist(project_root: Path, tag_suffix: str) -> None:
    """Assert that build/dev/prod images exist for the expected tag suffix."""
    for image_name in _expected_image_names(
        project_root=project_root, tag_suffix=tag_suffix
    ):
        assert _docker_image_exists(image_name=image_name), (
            f"Expected docker image {image_name!r} to exist."
        )


def _docker_image_exists(image_name: str) -> bool:
    """Determine whether a Docker image exists locally."""
    return (
        run(
            args=["docker", "image", "inspect", image_name],
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def _create_and_checkout_branch(
    repo: Repo, remote_repo: Repo, branch_name: str
) -> Head:
    """Create and check out a branch in the provided repository."""
    remote_repo.create_head(branch_name)
    repo.remote().fetch()
    repo.git.checkout(branch_name)
    return repo.active_branch


def test_make_setup_commands_build_unsuffixed_images_on_main(
    mock_project_root: Path,
    mock_lightweight_project: Repo,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
) -> None:
    """On main, setup commands should build unsuffixed image tags."""
    mock_lightweight_project.git.checkout(PRIMARY_BRANCH_NAME)
    setup_dev_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_dev_env"],
        cwd=mock_project_root,
        test_name="test_make_setup_commands_build_unsuffixed_images_on_main_setup_dev_env",
        real_project_root_dir=real_project_root_dir,
    )
    assert setup_dev_return_code == 0
    setup_prod_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_prod_env"],
        cwd=mock_project_root,
        test_name="test_make_setup_commands_build_unsuffixed_images_on_main_setup_prod_env",
        real_project_root_dir=real_project_root_dir,
    )
    assert setup_prod_return_code == 0
    _assert_expected_images_exist(project_root=mock_project_root, tag_suffix="")


def test_make_setup_commands_build_ticket_scoped_images_on_non_main(
    mock_project_root: Path,
    make_command_prefix: list[str],
    mock_new_branch: Head,
    current_ticket_id: str,
    real_project_root_dir: Path,
) -> None:
    """On non-main branches, setup commands should build ``-<ticket_id>`` tags."""
    assert mock_new_branch.name.startswith(current_ticket_id)
    setup_dev_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_dev_env"],
        cwd=mock_project_root,
        test_name=(
            "test_make_setup_commands_build_ticket_scoped_images_on_non_main_"
            "setup_dev_env"
        ),
        real_project_root_dir=real_project_root_dir,
    )
    assert setup_dev_return_code == 0
    setup_prod_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_prod_env"],
        cwd=mock_project_root,
        test_name=(
            "test_make_setup_commands_build_ticket_scoped_images_on_non_main_"
            "setup_prod_env"
        ),
        real_project_root_dir=real_project_root_dir,
    )
    assert setup_prod_return_code == 0
    _assert_expected_images_exist(
        project_root=mock_project_root, tag_suffix=f"-{current_ticket_id}"
    )


def test_different_ticket_branches_build_different_image_tags(
    mock_project_root: Path,
    mock_lightweight_project: Repo,
    mock_remote_git_repo: Repo,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
) -> None:
    """Different ticket branches should build different image tag names."""
    first_ticket_id = "TEST001"
    second_ticket_id = "TEST002"

    first_branch = _create_and_checkout_branch(
        repo=mock_lightweight_project,
        remote_repo=mock_remote_git_repo,
        branch_name=f"{first_ticket_id}-first-branch",
    )
    assert first_branch.name.startswith(first_ticket_id)
    first_setup_build_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_build_env"],
        cwd=mock_project_root,
        test_name="test_different_ticket_branches_build_different_image_tags_first",
        real_project_root_dir=real_project_root_dir,
    )
    assert first_setup_build_return_code == 0

    second_branch = _create_and_checkout_branch(
        repo=mock_lightweight_project,
        remote_repo=mock_remote_git_repo,
        branch_name=f"{second_ticket_id}-second-branch",
    )
    assert second_branch.name.startswith(second_ticket_id)
    second_setup_build_return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "CI_CD_FEATURE_TEST_MODE_FLAG=", "setup_build_env"],
        cwd=mock_project_root,
        test_name="test_different_ticket_branches_build_different_image_tags_second",
        real_project_root_dir=real_project_root_dir,
    )
    assert second_setup_build_return_code == 0

    project_name = get_project_name(project_root=mock_project_root)
    first_image = f"{project_name}:build-{first_ticket_id}"
    second_image = f"{project_name}:build-{second_ticket_id}"
    assert first_image != second_image
    assert _docker_image_exists(image_name=first_image)
    assert _docker_image_exists(image_name=second_image)
