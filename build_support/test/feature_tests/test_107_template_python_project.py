"""Feature tests for branch-scoped Docker image tags."""

from pathlib import Path
from subprocess import PIPE, Popen

from git import Head, Repo

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.build_paths import get_git_info_yaml
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_image_name
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.report_build_var import AllowedCliArgs


def _get_make_variable_value(project_root: Path, variable_name: str) -> str:
    """Evaluate and return a single Make variable.

    Args:
        project_root (Path): Root of the project to run ``make`` in.
        variable_name (str): Variable name to inspect.

    Returns:
        str: The evaluated variable value.
    """
    command = Popen(
        args=[
            "make",
            "--no-print-directory",
            "-s",
            "--eval",
            f"print-var: ; @echo $({variable_name})",
            "print-var",
        ],
        cwd=project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = command.communicate()
    if command.returncode != 0:
        msg = (
            f"Unable to inspect make variable '{variable_name}'.\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )
        raise RuntimeError(msg)
    return stdout.strip()


def _assert_expected_images(project_root: Path, tag_suffix: str) -> None:
    """Assert expected Docker image variables for the current checked out branch.

    Args:
        project_root (Path): Root of the project to inspect.
        tag_suffix (str): Expected tag suffix (for example ``-TEST001`` or ````).

    Returns:
        None
    """
    project_name = get_project_name(project_root=project_root)
    expected_images = {
        "DOCKER_BUILD_IMAGE": f"{project_name}:build{tag_suffix}",
        "DOCKER_DEV_IMAGE": f"{project_name}:dev{tag_suffix}",
        "DOCKER_PROD_IMAGE": f"{project_name}:prod{tag_suffix}",
        "DOCKER_PULUMI_IMAGE": f"{project_name}:pulumi{tag_suffix}",
    }
    for image_var, expected_image in expected_images.items():
        assert (
            _get_make_variable_value(project_root=project_root, variable_name=image_var)
            == expected_image
        )


def _checkout_new_branch(repo: Repo, remote_repo: Repo, branch_name: str) -> None:
    """Create and checkout a new branch on the mock project repository.

    Args:
        repo (Repo): Local mock project repository.
        remote_repo (Repo): Mock remote repository.
        branch_name (str): Name of branch to create/check out.

    Returns:
        None
    """
    remote_repo.create_head(branch_name)
    repo.remote().fetch()
    repo.git.checkout(branch_name)


def _run_report_build_var(project_root: Path, build_var: AllowedCliArgs) -> str:
    """Execute ``report_build_var.py`` and return the reported command.

    Args:
        project_root (Path): Root of the project to inspect.
        build_var (AllowedCliArgs): The CLI variable to report.

    Returns:
        str: The command string printed by ``report_build_var.py``.
    """
    command = Popen(
        args=[
            "python",
            "build_support/src/build_support/report_build_var.py",
            "--build-variable-to-report",
            build_var.value,
            "--non-docker-project-root",
            str(project_root),
            "--docker-project-root",
            str(project_root),
        ],
        cwd=project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = command.communicate()
    if command.returncode != 0:
        msg = (
            "Unable to report build variable.\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )
        raise RuntimeError(msg)
    return stdout.strip()


def _write_git_info_for_current_branch(project_root: Path, repo: Repo) -> None:
    """Write ``git_info.yaml`` for the repo's currently checked out branch.

    Args:
        project_root (Path): Root of the mock project.
        repo (Repo): Repository whose active branch should be captured.

    Returns:
        None
    """
    git_info = GitInfo(
        branch=repo.active_branch.name,
        tags=[],
        modified_subprojects=[],
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )
    git_info_yaml = get_git_info_yaml(project_root=project_root)
    git_info_yaml.parent.mkdir(parents=True, exist_ok=True)
    git_info_yaml.write_text(git_info.to_yaml())


def test_makefile_docker_images_are_unsuffixed_on_main(
    mock_project_root: Path, mock_lightweight_project: Repo
) -> None:
    """Ensure Docker image tags stay unchanged when the current branch is ``main``."""
    mock_lightweight_project.git.checkout(GitInfo.get_primary_branch_name())
    _assert_expected_images(project_root=mock_project_root, tag_suffix="")


def test_makefile_docker_images_are_ticket_scoped_on_non_main(
    mock_project_root: Path, mock_new_branch: Head, current_ticket_id: str
) -> None:
    """Ensure Docker image tags get ``-<ticket_id>`` on non-main branches."""
    assert mock_new_branch.name.startswith(current_ticket_id)
    _assert_expected_images(
        project_root=mock_project_root, tag_suffix=f"-{current_ticket_id}"
    )


def test_build_support_docker_vars_are_unsuffixed_on_main(
    mock_project_root: Path, mock_lightweight_project: Repo
) -> None:
    """Ensure build_support image naming uses unsuffixed tags on ``main``."""
    mock_lightweight_project.git.checkout(GitInfo.get_primary_branch_name())
    _write_git_info_for_current_branch(
        project_root=mock_project_root, repo=mock_lightweight_project
    )
    project_name = get_project_name(project_root=mock_project_root)
    assert (
        get_docker_image_name(
            project_root=mock_project_root, target_image=DockerTarget.DEV
        )
        == f"{project_name}:dev"
    )
    assert (
        get_docker_image_name(
            project_root=mock_project_root, target_image=DockerTarget.PROD
        )
        == f"{project_name}:prod"
    )


def test_build_support_docker_vars_are_ticket_scoped_on_non_main(
    mock_project_root: Path, mock_new_branch: Head, current_ticket_id: str
) -> None:
    """Ensure build_support image naming uses ``-<ticket_id>`` off ``main``."""
    assert mock_new_branch.name.startswith(current_ticket_id)
    _write_git_info_for_current_branch(
        project_root=mock_project_root, repo=mock_new_branch.repo
    )
    project_name = get_project_name(project_root=mock_project_root)
    assert (
        get_docker_image_name(
            project_root=mock_project_root, target_image=DockerTarget.DEV
        )
        == f"{project_name}:dev-{current_ticket_id}"
    )
    assert (
        get_docker_image_name(
            project_root=mock_project_root, target_image=DockerTarget.PROD
        )
        == f"{project_name}:prod-{current_ticket_id}"
    )


def test_report_build_var_uses_ticket_scoped_dev_image_on_non_main(
    mock_project_root: Path, mock_new_branch: Head, current_ticket_id: str
) -> None:
    """Ensure the report_build_var path resolves branch-scoped image tags."""
    assert mock_new_branch.name.startswith(current_ticket_id)
    _write_git_info_for_current_branch(
        project_root=mock_project_root, repo=mock_new_branch.repo
    )
    project_name = get_project_name(project_root=mock_project_root)
    reported_command = _run_report_build_var(
        project_root=mock_project_root,
        build_var=AllowedCliArgs.DEV_DOCKER_INTERACTIVE,
    )
    assert f"{project_name}:dev-{current_ticket_id}" in reported_command


def test_different_ticket_branches_generate_different_docker_image_tags(
    mock_project_root: Path,
    mock_lightweight_project: Repo,
    mock_remote_git_repo: Repo,
) -> None:
    """Ensure different ticket branches resolve to different Docker tags."""
    first_ticket_id = "TEST001"
    second_ticket_id = "TEST002"
    _checkout_new_branch(
        repo=mock_lightweight_project,
        remote_repo=mock_remote_git_repo,
        branch_name=f"{first_ticket_id}-first-branch",
    )
    first_tag = _get_make_variable_value(
        project_root=mock_project_root, variable_name="DOCKER_DEV_IMAGE"
    )

    _checkout_new_branch(
        repo=mock_lightweight_project,
        remote_repo=mock_remote_git_repo,
        branch_name=f"{second_ticket_id}-second-branch",
    )
    second_tag = _get_make_variable_value(
        project_root=mock_project_root, variable_name="DOCKER_DEV_IMAGE"
    )

    assert first_tag.endswith(f"-{first_ticket_id}")
    assert second_tag.endswith(f"-{second_ticket_id}")
    assert first_tag != second_tag
