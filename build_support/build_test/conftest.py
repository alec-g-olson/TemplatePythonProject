from pathlib import Path

import pytest
from build_tasks.common_build_tasks import GitInfo
from common_vars import PROJECT_ROOT_DIR


@pytest.fixture(scope="session")
def project_root_dir() -> Path:
    """Return the root directory of this project."""
    return PROJECT_ROOT_DIR


@pytest.fixture(scope="session")
def project_build_dir(project_root_dir: Path) -> Path:
    """Return the build directory of this project."""
    return project_root_dir.joinpath("build")


@pytest.fixture(scope="session")
def git_info_file(project_build_dir: Path) -> Path:
    """Return the build directory of this project."""
    return project_build_dir.joinpath("git_info.json")


@pytest.fixture(scope="session")
def git_info(git_info_file: Path) -> GitInfo:
    """Return the git information at the time of this test."""
    return GitInfo.from_json(git_info_file.read_text())


@pytest.fixture(scope="session")
def is_on_main(git_info: GitInfo):
    """Determine if the main branch is currently checked out."""
    return git_info.branch == "main"
