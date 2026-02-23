"""Feature tests for ticket 97: development container uses uv and not poetry.

Verifies that the development Docker image has ``uv`` available and ``poetry``
unavailable, so all future development uses uv for dependency management.
"""

from pathlib import Path
from subprocess import run

import pytest
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_image_name


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_dev_container_has_uv_not_poetry(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """Verify poetry is not available and uv is available in the dev container.

    Runs ``poetry --version`` and ``uv --version`` in the development
    container. Poetry must fail with a command-not-found style error;
    uv must succeed.

    Args:
        mock_project_root (Path): Root of the mock project (dev image context).
        make_command_prefix (list[str]): Make command prefix for running setup_dev_env.
        real_project_root_dir (Path): Root of the real project for image name lookup.
    """
    run(
        [*make_command_prefix, "setup_dev_env"],
        cwd=mock_project_root,
        check=True,
        capture_output=True,
    )
    image = get_docker_image_name(
        project_root=real_project_root_dir, target_image=DockerTarget.DEV
    )
    mount = f"{mock_project_root.resolve()}:/usr/dev"
    docker_run = ["docker", "run", "--rm", "-v", mount, "-w", "/usr/dev", image]

    poetry_result = run(
        [*docker_run, "poetry", "--version"],
        check=False,
        capture_output=True,
        text=True,
        cwd=mock_project_root,
    )
    assert poetry_result.returncode != 0, (
        "poetry should not be available in the dev container; "
        f"stderr: {poetry_result.stderr!r}"
    )
    assert (
        "not found" in poetry_result.stderr.lower()
        or "no such file" in poetry_result.stderr.lower()
    ), (
        "Expected command-not-found style error from poetry; "
        f"stderr: {poetry_result.stderr!r}"
    )

    uv_result = run(
        [*docker_run, "uv", "--version"],
        check=False,
        capture_output=True,
        text=True,
        cwd=mock_project_root,
    )
    assert uv_result.returncode == 0, (
        f"uv must be available in the dev container; stderr: {uv_result.stderr!r}"
    )
