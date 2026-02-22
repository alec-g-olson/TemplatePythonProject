from collections.abc import Iterator
from os import environ
from pathlib import Path
from pwd import getpwuid
from typing import cast
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest
from tomlkit import TOMLDocument, document, table

from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_vars.project_structure import (
    get_poetry_lock_file,
    get_pyproject_toml,
)

# Test parameterization constants
mock_project_versions = ["0.0.0", "0.0.1", "0.1.0", "1.0.0", "1.0.0-dev.1"]
mock_project_names = ["project_one", "project_two"]
mock_local_user_ids = [(0, 0), (2, 1)]


@pytest.fixture
def mock_project_versions_list() -> list[str]:
    """Returns the list of mock project versions for testing."""
    return mock_project_versions


@pytest.fixture(params=mock_project_versions)
def project_version(request: SubRequest) -> str:
    """The version contained in the pyproject toml."""
    return cast(str, request.param)


@pytest.fixture(params=mock_project_names)
def project_name(request: SubRequest) -> str:
    """The project name contained in the pyproject toml."""
    return cast(str, request.param)


@pytest.fixture(params=mock_local_user_ids)
def local_id_pairs(request: SubRequest) -> tuple[int, int]:
    """The local user uid and gid as a pair."""
    return cast(tuple[int, int], request.param)


@pytest.fixture
def local_uid(local_id_pairs: tuple[int, int]) -> int:
    """The uid of the local user."""
    return local_id_pairs[0]


@pytest.fixture
def local_gid(local_id_pairs: tuple[int, int]) -> int:
    """The gid of the local user."""
    return local_id_pairs[1]


@pytest.fixture
def local_user_env(local_uid: int, local_gid: int) -> dict[str, str] | None:
    if local_uid or local_gid:
        env = environ.copy()
        env["HOME"] = f"/home/{getpwuid(local_uid).pw_name}/"
        return env
    return None


@pytest.fixture(autouse=True)
def mock_current_branch_ticket_id_for_unit_tests() -> Iterator[None]:
    """Use main-branch-equivalent ticket lookup for unit tests by default."""
    with patch(
        "build_support.ci_cd_vars.docker_vars.get_ticket_id"
    ) as get_ticket_id_mock:
        get_ticket_id_mock.return_value = None
        yield


@pytest.fixture
def basic_task_info(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
    local_user_env: dict[str, str],
) -> BasicTaskInfo:
    """Provides basic task info for setting up and testing tasks."""
    return BasicTaskInfo(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_uid=local_uid,
        local_gid=local_gid,
        local_user_env=local_user_env,
    )


@pytest.fixture
def pyproject_toml_data(project_version: str, project_name: str) -> TOMLDocument:
    """The TOMLDocument that would be read from the pyproject toml."""
    doc = document()
    doc["tool"] = table()
    tool = doc["tool"]
    tool["poetry"] = table()  # type: ignore[index]
    tool["poetry"]["name"] = project_name  # type: ignore[index]
    tool["poetry"]["version"] = project_version  # type: ignore[index]

    tool["coverage"] = table()  # type: ignore[index]
    tool["coverage"]["run"] = table()  # type: ignore[index]
    tool["coverage"]["run"]["branch"] = True  # type: ignore[index]
    tool["coverage"]["run"]["parallel"] = True  # type: ignore[index]
    tool["coverage"]["run"]["concurrency"] = [  # type: ignore[index]
        "multiprocessing",
        "thread",
    ]

    tool["coverage"]["report"] = table()  # type: ignore[index]
    tool["coverage"]["report"]["fail_under"] = 100  # type: ignore[index]
    tool["coverage"]["report"]["exclude_lines"] = [  # type: ignore[index]
        "pragma: no cov"
    ]

    return doc


@pytest.fixture
def pyproject_toml_contents(project_version: str, project_name: str) -> str:
    """The contents of a pyproject toml to be used in testing."""
    return f"""[tool.poetry]
name = "{project_name}"
version = "{project_version}"

[tool.coverage.run]
branch = true
parallel = true
concurrency = ["multiprocessing", "thread"]

[tool.coverage.report]
fail_under = 100
exclude_lines = [
  "pragma: no cov"
]"""


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
def pulumi_version(request: SubRequest) -> str:
    """The version contained in the pyproject toml."""
    return cast(str, request.param)


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
