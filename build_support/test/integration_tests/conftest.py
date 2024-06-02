import shutil
from pathlib import Path

import pytest
import yaml
from git import Head, Repo

from build_support.ci_cd_vars.file_and_dir_path_vars import get_local_info_yaml
from build_support.ci_cd_vars.git_status_vars import (
    monkeypatch_git_python_execute_kwargs,
)
from build_support.ci_cd_vars.project_structure import (
    get_build_dir,
    get_integration_test_scratch_folder,
    maybe_build_dir,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
)


def remove_dir_and_all_contents(path: Path) -> None:
    for sub in path.iterdir():
        if sub.is_dir():
            remove_dir_and_all_contents(path=sub)
        else:
            sub.unlink()
    path.rmdir()


@pytest.fixture()
def make_command_prefix(
    mock_project_root: Path, real_project_root_dir: Path, mock_remote_git_folder: Path
) -> list[str]:
    docker_project_root = real_project_root_dir
    test_project_relative_root = mock_project_root.relative_to(docker_project_root)
    remote_repo_relative_root = mock_remote_git_folder.relative_to(docker_project_root)
    non_docker_project_root = Path(
        yaml.safe_load(
            get_local_info_yaml(project_root=real_project_root_dir).read_text()
        )["non_docker_project_root"]
    )
    test_non_docker_root = non_docker_project_root.joinpath(test_project_relative_root)
    remote_repo_non_docker_root = non_docker_project_root.joinpath(
        remote_repo_relative_root
    )
    return [
        "make",
        f"NON_DOCKER_ROOT={test_non_docker_root}",
        f"GIT_MOUNT=-v {remote_repo_non_docker_root}:{mock_remote_git_folder}",
        "CI_CD_INTEGRATION_TEST_MODE_FLAG=--ci-cd-integration-test-mode",
    ]


@pytest.fixture()
def mock_lightweight_project(
    mock_project_root: Path, mock_remote_git_repo: Repo, real_project_root_dir: Path
) -> Repo:
    monkeypatch_git_python_execute_kwargs()
    remote_repo_url = str(mock_remote_git_repo.working_dir)
    repo = Repo.clone_from(url=remote_repo_url, to_path=mock_project_root)
    repo.remote().push()
    integration_scratch_name = get_integration_test_scratch_folder(
        project_root=mock_project_root
    ).name
    # copy everything from real project
    for file_or_folder in real_project_root_dir.glob("*"):
        name = file_or_folder.name
        if name not in [".git", integration_scratch_name]:
            dest = mock_project_root.joinpath(name)
            if file_or_folder.is_dir():
                shutil.copytree(src=file_or_folder, dst=dest)
            else:
                shutil.copy(src=file_or_folder, dst=dest)
    build_folder_name = get_build_dir(project_root=mock_project_root).name
    local_info_name = get_local_info_yaml(project_root=mock_project_root).name
    for file_or_folder in mock_project_root.joinpath(build_folder_name).glob("*"):
        name = file_or_folder.name
        if name != local_info_name:
            if file_or_folder.is_dir():
                shutil.rmtree(path=file_or_folder)
            else:
                file_or_folder.unlink()

    # turn non-build_subprojects into lightweight minimal projects
    init_name = "__init__.py"
    for subproject_context, subproject in get_all_python_subprojects_dict(
        project_root=mock_project_root
    ).items():
        if subproject_context != SubprojectContext.BUILD_SUPPORT:
            remove_dir_and_all_contents(path=subproject.get_root_dir())
            maybe_build_dir(dir_to_build=subproject.get_src_dir())
            pkg_dir = maybe_build_dir(dir_to_build=subproject.get_python_package_dir())
            maybe_build_dir(dir_to_build=subproject.get_test_dir())
            unit_test_dir = maybe_build_dir(
                dir_to_build=subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                )
            )
            integration_test_dir = maybe_build_dir(
                dir_to_build=subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                )
            )
            integration_test_dir.joinpath(init_name).touch()
            pkg_dir.joinpath(init_name).write_text('"""Top level package."""')
            unit_test_dir.joinpath(init_name).touch()
    repo.git.add(update=True)
    repo.index.commit("initial lightweight project commit")
    repo.remote().push()
    tag_name = "0.0.0"
    repo.create_tag(tag_name)
    repo.remote().push(tag_name)
    return repo


@pytest.fixture()
def current_ticket_name() -> str:
    return "TEST001"


@pytest.fixture()
def mock_new_branch(
    mock_remote_git_repo: Repo, mock_lightweight_project: Repo, current_ticket_name: str
) -> Head:
    branch_name = f"{current_ticket_name}-some-ticket-description"
    mock_remote_git_repo.create_head(branch_name)
    mock_lightweight_project.remote().fetch()
    mock_lightweight_project.git.checkout(branch_name)
    return mock_lightweight_project.active_branch
