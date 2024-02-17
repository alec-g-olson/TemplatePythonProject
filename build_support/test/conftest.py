from pathlib import Path
from typing import Any

import pytest
from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_git_info_yaml,
    get_poetry_lock_file,
    get_pyproject_toml,
)


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
mock_local_user_ids = [(1, 20), (1337, 42)]


@pytest.fixture(params=mock_project_versions, scope="session")
def project_version(request) -> str:
    """The version contained in the pyproject toml."""
    return request.param


@pytest.fixture(params=mock_project_names, scope="session")
def project_name(request) -> str:
    """The project name contained in the pyproject toml."""
    return request.param


@pytest.fixture(params=mock_local_user_ids, scope="session")
def local_uid(request) -> str:
    """The name of the local user."""
    return request.param[0]


@pytest.fixture(params=mock_local_user_ids, scope="session")
def local_gid(request) -> str:
    """The name of the local user."""
    return request.param[1]


@pytest.fixture
def docker_project_root(tmp_path: Path) -> Path:
    """Provides a temp directory to use as the project root within docker containers."""
    docker_project_root = tmp_path.joinpath("usr", "dev")
    docker_project_root.mkdir(parents=True, exist_ok=True)
    return docker_project_root


@pytest.fixture(scope="session")
def pyproject_toml_data(project_version: str, project_name: str) -> dict[Any, Any]:
    """The dictionary that would be read from the pyproject toml."""
    return {"tool": {"poetry": {"name": project_name, "version": project_version}}}


@pytest.fixture(scope="session")
def pyproject_toml_contents(project_version: str, project_name: str) -> str:
    """The contents of a pyproject toml to be used in testing."""
    return f'[tool.poetry]\nname = "{project_name}"\nversion = "{project_version}"'


@pytest.fixture
def mock_local_pyproject_toml_file(
    pyproject_toml_contents: str, mock_project_root: Path
) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_pyproject_toml_file = get_pyproject_toml(project_root=mock_project_root)
    mock_pyproject_toml_file.write_text(pyproject_toml_contents)
    return mock_pyproject_toml_file


@pytest.fixture
def mock_docker_pyproject_toml_file(
    pyproject_toml_contents: str, docker_project_root: Path
) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_pyproject_toml_file = get_pyproject_toml(project_root=docker_project_root)
    mock_pyproject_toml_file.write_text(pyproject_toml_contents)
    return mock_pyproject_toml_file


mock_pulumi_versions = ["0.0.0", "0.0.1", "0.1.0", "1.0.0"]
other_package_info = '[[package]]\nname = "other_package"\nversion = "1.0.0"\n\n'


@pytest.fixture(params=mock_pulumi_versions)
def pulumi_version(request) -> str:
    """The version contained in the pyproject toml."""
    return request.param


@pytest.fixture
def poetry_lock_contents(pulumi_version: str) -> str:
    """The contents of a pyproject toml to be used in testing."""
    return (
        other_package_info
        + f'[[package]]\nname = "pulumi"\nversion = "{pulumi_version}"'
    )


@pytest.fixture
def mock_local_poetry_lock_file(
    poetry_lock_contents: str, mock_project_root: Path
) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_poetry_lock_file = get_poetry_lock_file(project_root=mock_project_root)
    mock_poetry_lock_file.write_text(poetry_lock_contents)
    return mock_poetry_lock_file


@pytest.fixture
def mock_docker_poetry_lock_file(
    poetry_lock_contents: str, docker_project_root: Path
) -> Path:
    """Creates a mock pyproject toml file for use in testing."""
    mock_poetry_lock_file = get_poetry_lock_file(project_root=docker_project_root)
    mock_poetry_lock_file.write_text(poetry_lock_contents)
    return mock_poetry_lock_file


@pytest.fixture(scope="session")
def real_git_info(real_project_root_dir: Path) -> GitInfo:
    """Return the git information at the time of this test."""
    return GitInfo.from_yaml(
        get_git_info_yaml(project_root=real_project_root_dir).read_text()
    )


@pytest.fixture(scope="session")
def is_on_main(real_git_info: GitInfo):
    """Determine if the main branch is currently checked out."""
    return real_git_info.branch == "main"
