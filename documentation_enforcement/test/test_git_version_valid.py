from pathlib import Path

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.project_setting_vars import (
    ALLOWED_VERSION_REGEX,
    get_project_version,
)


@pytest.fixture(scope="session")
def current_version(real_project_root_dir: Path) -> str:
    """The version in the pyproject.toml file."""
    return get_project_version(project_root=real_project_root_dir)


def test_current_version_valid(current_version: str) -> None:
    assert current_version[0] == "v"
    assert ALLOWED_VERSION_REGEX.match(current_version[1:])


def test_current_version_has_not_been_used(
    current_version: str, real_git_info: GitInfo
) -> None:
    assert current_version not in real_git_info.tags
