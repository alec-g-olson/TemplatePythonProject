from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

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
