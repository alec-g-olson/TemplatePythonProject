"""Shared fixtures for PYPI feature tests."""

import os
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_image_name
from build_support.ci_cd_vars.project_structure import (
    get_feature_test_scratch_folder,
    maybe_build_dir,
)


def _sanitize_test_id(node_name: str) -> str:
    """Sanitize pytest node name for use as a directory name."""
    return node_name.replace("[", "_").replace("]", "_").replace("::", "_").rstrip("_")


@pytest.fixture
def prod_workdir() -> str:
    """Path inside the prod container where host_tmp_path is mounted."""
    return "/usr/workdir"


@pytest.fixture
def pypi_feature_test_scratch_path(request: SubRequest) -> Path:
    """Per-test scratch dir under test_scratch_folder for file I/O and prod -v mount.

    Uses test_scratch_folder/pypi_prod_scratch/<test_id> so the path is stable and
    under the project root for correct host-path translation when running in dev.
    """
    project_root = Path(os.environ.get("DOCKER_REMOTE_PROJECT_ROOT") or Path.cwd())
    scratch_base = get_feature_test_scratch_folder(project_root=project_root)
    test_id = _sanitize_test_id(request.node.name)
    return maybe_build_dir(
        dir_to_build=scratch_base.joinpath("pypi_prod_scratch", test_id)
    )


@pytest.fixture
def host_tmp_path(pypi_feature_test_scratch_path: Path) -> Path:
    """Path to the scratch dir as seen by the host Docker daemon for -v mount.

    When running inside a dev container, returns the host path so the daemon can
    mount it. Otherwise returns the scratch path as-is.
    """
    scratch_path = pypi_feature_test_scratch_path
    non_docker_root = os.environ.get("NON_DOCKER_PROJECT_ROOT")
    docker_root = os.environ.get("DOCKER_REMOTE_PROJECT_ROOT", "/usr/dev")
    if non_docker_root is not None and str(scratch_path).startswith(docker_root):
        return Path(non_docker_root) / scratch_path.relative_to(docker_root)
    return scratch_path


@pytest.fixture
def prod_docker_command_prefix(host_tmp_path: Path, prod_workdir: str) -> list[str]:
    """Docker run prefix for prod image with tmp dir mounted at prod_workdir."""
    docker_project_root = Path(os.environ.get("DOCKER_REMOTE_PROJECT_ROOT", "/usr/dev"))
    image = get_docker_image_name(
        project_root=docker_project_root, target_image=DockerTarget.PROD
    )
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "host",
        "-i",
        "-v",
        f"{host_tmp_path}:{prod_workdir}",
        "-w",
        prod_workdir,
        image,
    ]
