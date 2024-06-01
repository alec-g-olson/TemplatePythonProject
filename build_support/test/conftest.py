from pathlib import Path
from typing import cast

import pytest
from _pytest.fixtures import SubRequest
from git import Repo

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import get_git_info_yaml
from build_support.ci_cd_vars.git_status_vars import MAIN_BRANCH_NAME
from build_support.ci_cd_vars.project_structure import maybe_build_dir
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
    return maybe_build_dir(dir_to_build=tmp_path.joinpath("local_project_root"))


@pytest.fixture()
def docker_project_root(tmp_path: Path) -> Path:
    """Provides a temp directory to use as the project root within docker containers."""
    return maybe_build_dir(dir_to_build=tmp_path.joinpath("usr", "dev"))


subproject_contexts = get_sorted_subproject_contexts()


@pytest.fixture(params=subproject_contexts)
def subproject_context(request: SubRequest) -> SubprojectContext:
    return cast(SubprojectContext, request.param)


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
def mock_remote_git_folder(tmp_path: Path) -> Path:
    return maybe_build_dir(dir_to_build=tmp_path.joinpath("remote_repo_root"))


@pytest.fixture()
def mock_remote_git_repo(mock_remote_git_folder: Path) -> Repo:
    repo = Repo.init(
        path=mock_remote_git_folder, bare=True, initial_branch=MAIN_BRANCH_NAME
    )
    repo.index.commit("initial remote commit")
    return repo
