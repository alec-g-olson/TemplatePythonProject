import re
import tomllib
from pathlib import Path

import pytest
from build_tasks.common_build_tasks import GitInfo

SEMVER_REGEX = re.compile(r"^v\d+\.\d+\.\d+(-dev\.\d+)?$")


@pytest.fixture(scope="session")
def pyproject_toml(project_root_dir: Path) -> Path:
    """Path to the pyproject.toml file."""
    return project_root_dir.joinpath("pyproject.toml")


@pytest.fixture(scope="session")
def current_version(pyproject_toml: Path) -> str:
    """The version in the pyproject.toml file."""
    pyproject_toml_data = tomllib.loads(pyproject_toml.read_text())
    return "v" + pyproject_toml_data["tool"]["poetry"]["version"]


def test_current_version_valid(current_version: str) -> None:
    assert SEMVER_REGEX.match(current_version)


def test_current_version_has_not_been_used(
    current_version: str, git_info: GitInfo
) -> None:
    assert current_version not in git_info.tags
