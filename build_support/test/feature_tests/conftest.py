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
    get_feature_test_scratch_folder,
    maybe_build_dir,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
)


def remove_dir_and_all_contents(path: Path) -> None:
    for sub in path.iterdir():
        if sub.is_dir():
            remove_dir_and_all_contents(path=sub)
        else:
            sub.unlink()
    path.rmdir()


@pytest.fixture
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
        "CI_CD_FEATURE_TEST_MODE_FLAG=--ci-cd-feature-test-mode",
    ]


@pytest.fixture(scope="session")
def mock_lightweight_project_copy_dir(real_build_dir: Path) -> Path:
    return maybe_build_dir(dir_to_build=real_build_dir.joinpath("lightweight_project"))


@pytest.fixture(scope="session")
def mock_lightweight_project_copy(
    mock_lightweight_project_copy_dir: Path, real_project_root_dir: Path
) -> Path:
    if mock_lightweight_project_copy_dir.exists():
        # If the lightweight copy already exists, return it
        remove_dir_and_all_contents(path=mock_lightweight_project_copy_dir)

    # Create the lightweight project copy
    feature_scratch_name = get_feature_test_scratch_folder(
        project_root=real_project_root_dir
    ).name
    build_folder_name = get_build_dir(project_root=real_project_root_dir).name

    # Copy everything from real project except .git, build, and scratch folders
    for file_or_folder in real_project_root_dir.glob("*"):
        name = file_or_folder.name
        if name not in [".git", ".idea", build_folder_name, feature_scratch_name]:
            dest = mock_lightweight_project_copy_dir.joinpath(name)
            if file_or_folder.is_dir():
                shutil.copytree(src=file_or_folder, dst=dest)
            else:
                shutil.copy(src=file_or_folder, dst=dest)

    # Turn non-build_support subprojects into lightweight minimal projects
    init_name = "__init__.py"
    for subproject_context, subproject in get_all_python_subprojects_dict(
        project_root=mock_lightweight_project_copy_dir
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
            feature_test_dir = maybe_build_dir(
                dir_to_build=subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
                )
            )
            feature_test_dir.joinpath(init_name).touch()
            pkg_dir.joinpath(init_name).write_text('"""Top level package."""')
            unit_test_dir.joinpath(init_name).touch()

    return mock_lightweight_project_copy_dir


@pytest.fixture
def mock_lightweight_project(
    docker_project_root: Path,
    mock_project_root: Path,
    mock_remote_git_repo: Repo,
    mock_lightweight_project_copy: Path,
) -> Repo:
    if mock_project_root.exists():
        remove_dir_and_all_contents(path=mock_project_root)

    monkeypatch_git_python_execute_kwargs()
    remote_repo_url = str(mock_remote_git_repo.working_dir)
    repo = Repo.clone_from(url=remote_repo_url, to_path=mock_project_root)
    repo.remote().push()

    # Configure Git to trust the repository directory
    repo.git.config("--global", "--add", "safe.directory", str(mock_project_root))
    repo.git.config("--global", "--add", "safe.directory", str(docker_project_root))

    # Copy everything from the cached lightweight project copy
    for file_or_folder in mock_lightweight_project_copy.iterdir():
        if file_or_folder.name != ".git":  # Don't overwrite the .git directory
            dest = mock_project_root.joinpath(file_or_folder.name)
            if file_or_folder.is_dir():
                shutil.copytree(src=file_or_folder, dst=dest)
            else:
                shutil.copy2(src=file_or_folder, dst=dest)

    # Commit the lightweight project to git
    repo.git.add(update=True)
    repo.index.commit("initial lightweight project commit")
    repo.remote().push()
    tag_name = "0.0.0"
    repo.create_tag(tag_name)
    repo.remote().push(tag_name)
    return repo


@pytest.fixture
def mock_lightweight_project_with_single_feature_test(
    mock_lightweight_project: Repo, mock_project_root: Path
) -> Repo:
    subproject = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=mock_project_root
    )
    feature_test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
    )
    feature_test_file = feature_test_dir.joinpath("test_empty_test.py")
    feature_test_file.write_text(
        "from time import sleep\n"
        "\n"
        "def test_something() -> None:\n"
        "    sleep(1)\n"
        "    assert True\n"
    )

    # Commit the lightweight project to git
    mock_lightweight_project.git.add(update=True)
    mock_lightweight_project.index.commit("added single lightweight feature test")
    mock_lightweight_project.remote().push()
    tag_name = "0.1.0"
    mock_lightweight_project.create_tag(tag_name)
    mock_lightweight_project.remote().push(tag_name)
    return mock_lightweight_project


@pytest.fixture
def mock_lightweight_project_with_unit_tests_and_feature_tests(
    mock_lightweight_project: Repo, mock_project_root: Path
) -> Repo:
    for subproject_context, subproject in get_all_python_subprojects_dict(
        project_root=mock_project_root
    ).items():
        subproject_pkg_dir = subproject.get_python_package_dir()
        subproject_src_file = subproject_pkg_dir.joinpath("src_file.py")
        subproject_src_file.write_text(
            "from time import sleep\n"
            "\n"
            "def add_slow(a: int, b: int) -> int:\n"
            "    sleep(0.5)\n"
            "    return a + b\n"
        )
        project_unit_test_dir = subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
        )
        project_unit_test_file = project_unit_test_dir.joinpath("test_src_file.py")
        project_unit_test_file.write_text(
            "from src_file import add_slow\n"
            "\n"
            "def test_add_slow() -> None:\n"
            "    assert add_slow(2, 3) == 5\n"
        )
        feature_test_dir = subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        )
        feature_test_file = feature_test_dir.joinpath("test_empty_test.py")
        feature_test_file.write_text(
            "from time import sleep\n"
            "\n"
            "def test_something() -> None:\n"
            "    sleep(1)\n"
            "    assert True\n"
        )

    # Commit the lightweight project to git
    mock_lightweight_project.git.add(update=True)
    mock_lightweight_project.index.commit("added single lightweight feature test")
    mock_lightweight_project.remote().push()
    tag_name = "0.1.0"
    mock_lightweight_project.create_tag(tag_name)
    mock_lightweight_project.remote().push(tag_name)
    return mock_lightweight_project


@pytest.fixture
def current_ticket_name() -> str:
    return "TEST001"


@pytest.fixture
def mock_new_branch(
    mock_remote_git_repo: Repo, mock_lightweight_project: Repo, current_ticket_name: str
) -> Head:
    branch_name = f"{current_ticket_name}-some-ticket-description"
    mock_remote_git_repo.create_head(branch_name)
    mock_lightweight_project.remote().fetch()
    mock_lightweight_project.git.checkout(branch_name)
    return mock_lightweight_project.active_branch
