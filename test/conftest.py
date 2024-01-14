from dataclasses import dataclass
from pathlib import Path

import pytest
from dataclasses_json import dataclass_json

PROJECT_ROOT_DIR = Path(__file__).parent.parent


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


@dataclass_json
@dataclass
class GitInfo:
    """An object containing the current git information."""

    branch: str


@pytest.fixture(scope="session")
def git_info(git_info_file: Path) -> GitInfo:
    """Return the git information at the time of this test."""
    with git_info_file.open() as git_info_data:
        return GitInfo.from_json(git_info_data.read())


@pytest.fixture(scope="session")
def is_on_main(git_info: GitInfo):
    """Determine if the main branch is currently checked out."""
    return git_info.branch == "main"
