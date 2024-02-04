from pathlib import Path
from typing import Any

import pytest
from build_tasks.env_setup_tasks import GitInfo
from build_vars.file_and_dir_path_vars import get_git_info_yaml, get_pyproject_toml


@pytest.fixture(scope="session")
def real_project_root_dir() -> Path:
    """Return the root directory of this project."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Mocks the project root for testing."""
    return tmp_path


mock_project_versions = ["0.0.0", "0.0.1", "0.1.0", "1.0.0", "1.0.0-dev.1"]
mock_project_names = ["project_one", "project_two"]
mock_local_usernames = ["user_one", "other_user"]


@pytest.fixture(params=mock_project_versions, scope="session")
def project_version(request) -> str:
    """The version contained in the pyproject toml."""
    return request.param


@pytest.fixture(params=mock_project_names, scope="session")
def project_name(request) -> str:
    """The project name contained in the pyproject toml."""
    return request.param


@pytest.fixture(params=mock_local_usernames, scope="session")
def local_username(request) -> str:
    """The name of the local user."""
    return request.param


@pytest.fixture
def docker_project_root(tmp_path) -> Path:
    return tmp_path.joinpath("usr", "dev")


@pytest.fixture(scope="session")
def pyproject_toml_data(project_version: str, project_name: str) -> dict[Any, Any]:
    """The dictionary that would be read from the pyproject toml."""
    return {"tool": {"poetry": {"name": project_name, "version": project_version}}}


@pytest.fixture(scope="session")
def pyproject_toml_contents(project_version: str, project_name: str) -> str:
    """The contents of a pyproject toml to be used in testing."""
    return f'[tool.poetry]\nname = "{project_name}"\nversion = "{project_version}"'


@pytest.fixture
def mock_local_pyproject_toml_file(pyproject_toml_contents, mock_project_root) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_pyproject_toml_file = get_pyproject_toml(project_root=mock_project_root)
    mock_pyproject_toml_file.write_text(pyproject_toml_contents)
    return mock_pyproject_toml_file


@pytest.fixture
def mock_docker_pyproject_toml_file(
    pyproject_toml_contents, docker_project_root
) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_pyproject_toml_file = get_pyproject_toml(project_root=docker_project_root)
    mock_pyproject_toml_file.parent.mkdir(parents=True, exist_ok=True)
    mock_pyproject_toml_file.write_text(pyproject_toml_contents)
    return mock_pyproject_toml_file


@pytest.fixture(scope="session")
def real_git_info(real_project_root_dir) -> GitInfo:
    """Return the git information at the time of this test."""
    return GitInfo.from_yaml(
        get_git_info_yaml(project_root=real_project_root_dir).read_text()
    )


@pytest.fixture(scope="session")
def is_on_main(real_git_info):
    """Determine if the main branch is currently checked out."""
    return real_git_info.branch == "main"
