from pathlib import Path

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import get_git_info_yaml


@pytest.fixture(scope="session")
def real_project_root_dir() -> Path:
    """Return the root directory of this project."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def real_git_info(real_project_root_dir: Path) -> GitInfo:
    """Return the git information at the time of this test."""
    return GitInfo.from_yaml(
        get_git_info_yaml(project_root=real_project_root_dir).read_text()
    )


@pytest.fixture(scope="session")
def is_on_main(real_git_info: GitInfo) -> bool:
    """Determine if the main branch is currently checked out."""
    return real_git_info.branch == GitInfo.get_primary_branch_name()
