from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import get_git_info_yaml
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
    get_sorted_subproject_contexts,
)


@pytest.fixture(scope="session")
def real_project_root_dir() -> Path:
    """Return the root directory of this project."""
    return Path(__file__).parent.parent.parent


@pytest.fixture()
def mock_project_root(tmp_path: Path) -> Path:
    """Mocks the project root for testing."""
    return tmp_path


@pytest.fixture()
def docker_project_root(tmp_path: Path) -> Path:
    """Provides a temp directory to use as the project root within docker containers."""
    docker_project_root = tmp_path.joinpath("usr", "dev")
    docker_project_root.mkdir(parents=True, exist_ok=True)
    return docker_project_root


subproject_contexts = get_sorted_subproject_contexts()


@pytest.fixture(params=subproject_contexts)
def subproject_context(request: SubRequest) -> SubprojectContext:
    return request.param


@pytest.fixture()
def mock_subproject(
    subproject_context: SubprojectContext, mock_project_root: Path
) -> PythonSubproject:
    return get_python_subproject(
        subproject_context=subproject_context, project_root=mock_project_root
    )


@pytest.fixture()
def mock_docker_subproject(
    subproject_context: SubprojectContext, docker_project_root: Path
) -> PythonSubproject:
    return get_python_subproject(
        subproject_context=subproject_context, project_root=docker_project_root
    )


@pytest.fixture(scope="session")
def real_git_info(real_project_root_dir: Path) -> GitInfo:
    """Return the git information at the time of this test."""
    return GitInfo.from_yaml(
        get_git_info_yaml(project_root=real_project_root_dir).read_text(),
    )


@pytest.fixture(scope="session")
def is_on_main(real_git_info: GitInfo) -> bool:
    """Determine if the main branch is currently checked out."""
    return real_git_info.branch == GitInfo.get_primary_branch_name()


@pytest.fixture()
def check_weblinks(is_on_main: bool) -> bool:
    return not is_on_main


@pytest.fixture()
def mock_lightweight_project(tmp_path: Path) -> Path:
    lightweight_project_root = tmp_path.joinpath("lightweight_project")
    lightweight_project_root.mkdir()
    return lightweight_project_root
