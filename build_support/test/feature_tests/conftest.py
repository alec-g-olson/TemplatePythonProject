"""Shared fixtures and helpers for feature tests.

Provides utilities for creating lightweight mock projects, running
inner ``make test`` invocations inside Docker containers, and
managing temporary git repositories used by the feature test suite.
"""

import shutil
from pathlib import Path

import pytest
import yaml
from git import Head, Repo

from build_support.ci_cd_vars.build_paths import get_local_info_yaml
from build_support.ci_cd_vars.git_status_vars import (
    monkeypatch_git_python_execute_kwargs,
)
from build_support.ci_cd_vars.project_setting_vars import get_project_name
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
    """Recursively remove a directory and all of its contents.

    Args:
        path (Path): The directory to remove.
    """
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
    """Build the ``make`` command prefix for running inner builds.

    Constructs a ``make`` invocation that targets the mock project
    instead of the real project, mounts the mock remote git repo,
    and enables ``--ci-cd-feature-test-mode`` to skip Docker image
    rebuilds inside the inner build.

    Args:
        mock_project_root (Path): Root of the mock project.
        real_project_root_dir (Path): Root of the real project.
        mock_remote_git_folder (Path): Path to the mock bare repo.

    Returns:
        list[str]: Command tokens for ``make`` with overrides.
    """
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
    """Return the directory path for the lightweight project cache.

    Args:
        real_build_dir (Path): The real project's build directory.

    Returns:
        Path: Path to the lightweight project copy directory.
    """
    return maybe_build_dir(dir_to_build=real_build_dir.joinpath("lightweight_project"))


@pytest.fixture(scope="session")
def mock_lightweight_project_copy(
    mock_lightweight_project_copy_dir: Path, real_project_root_dir: Path
) -> Path:
    """Create a cached lightweight copy of the real project.

    Copies the real project tree (excluding ``.git``, ``.idea``,
    build, and scratch directories) and strips non-build-support
    subprojects down to minimal skeletons with empty ``__init__.py``
    files. This session-scoped copy is reused across tests to avoid
    redundant filesystem work.

    Args:
        mock_lightweight_project_copy_dir (Path): Destination dir.
        real_project_root_dir (Path): Real project root.

    Returns:
        Path: The populated lightweight project copy directory.
    """
    if mock_lightweight_project_copy_dir.exists():
        # If the lightweight copy already exists, return it
        remove_dir_and_all_contents(path=mock_lightweight_project_copy_dir)

    # Ensure the directory exists
    mock_lightweight_project_copy_dir.mkdir(parents=True, exist_ok=True)

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
            pkg_dir.joinpath(init_name).write_text('"""Top level package."""\n')
            unit_test_dir.joinpath(init_name).touch()

    return mock_lightweight_project_copy_dir


@pytest.fixture
def mock_lightweight_project(
    docker_project_root: Path,
    mock_project_root: Path,
    mock_remote_git_repo: Repo,
    mock_lightweight_project_copy: Path,
) -> Repo:
    """Create a fresh git-tracked mock project for a single test.

    Clones the mock remote repo, overlays the cached lightweight
    project copy onto it, commits, pushes, and tags ``0.0.0``. The
    resulting repo is ready for a test to modify files and run
    ``make test`` against.

    Args:
        docker_project_root (Path): Docker project root path.
        mock_project_root (Path): Where to create the mock repo.
        mock_remote_git_repo (Repo): The mock bare remote repo.
        mock_lightweight_project_copy (Path): Cached project copy.

    Returns:
        Repo: The initialised mock project git repository.
    """
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
    """Add a single feature test to the PYPI subproject.

    Creates a minimal feature test file, commits it with tag
    ``0.1.0``, and pushes to the remote.

    Args:
        mock_lightweight_project (Repo): The mock project repo.
        mock_project_root (Path): Root of the mock project.

    Returns:
        Repo: The updated mock project repository.
    """
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

    # Commit the feature test to the lightweight git project
    mock_lightweight_project.index.add([str(feature_test_file)])
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
    """Add source, unit tests, and feature tests to the mock project.

    Populates the PYPI subproject with a source module, a matching
    unit test file, and a feature test. All generated Python files
    must include module-level docstrings and Google-style function
    docstrings with typed ``Args`` and ``Returns`` sections, because
    the inner ``make test`` enforces ruff and style-enforcement
    checks against the mounted mock project files.

    Args:
        mock_lightweight_project (Repo): The mock project repo.
        mock_project_root (Path): Root of the mock project.

    Returns:
        Repo: The updated mock project repository.
    """
    for subproject in [
        get_python_subproject(SubprojectContext.PYPI, mock_project_root)
    ]:
        subproject_pkg_dir = subproject.get_python_package_dir()
        subproject_pkg_init_file = subproject_pkg_dir.joinpath("__init__.py")
        subproject_pkg_init_file.write_text(
            '''"""Top level package.

Modules:
    | src_file: A simple source file for testing purposes.
"""
'''
        )
        subproject_src_file = subproject_pkg_dir.joinpath("src_file.py")
        subproject_src_file.write_text(
            '''"""A simple Python module for testing purposes."""

from time import sleep


def add_slow(a: int, b: int) -> int:
    """Adds two numbers slowly.

    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of the two numbers.
    """
    sleep(0.5)
    return a + b
'''
        )
        project_unit_test_dir = subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
        )
        project_unit_test_file = project_unit_test_dir.joinpath("test_src_file.py")
        project_name = get_project_name(project_root=mock_project_root)
        project_unit_test_file.write_text(
            f"""from {project_name}.src_file import add_slow


def test_add_slow() -> None:
    a = 2
    b = 3
    expected_sum = 5
    assert add_slow(a=a, b=b) == expected_sum
"""
        )
        feature_test_dir = subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        )
        feature_test_file = feature_test_dir.joinpath("test_empty_test.py")
        feature_test_file.write_text(
            """from time import sleep


def test_something() -> None:
    sleep(1)
    assert True
"""
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
def current_ticket_id() -> str:
    """Return a fixed ticket id for mock branch creation.

    Returns:
        str: The ticket id ``TEST001``.
    """
    return "TEST001"


@pytest.fixture(
    params=["", "branch-description"], ids=["id-only-branch", "described-branch"]
)
def current_branch_name(request: pytest.FixtureRequest, current_ticket_id: str) -> str:
    """Build a branch name from the current ticket id.

    Args:
        request (pytest.FixtureRequest): Access to the requested fixture variant.
        current_ticket_id (str): The ticket id to embed in the branch name.

    Returns:
        str: Either ``<ticket_id>`` or ``<ticket_id>-some-ticket-description``.
    """
    return (
        f"{current_ticket_id}-{request.param}" if request.param else current_ticket_id
    )


@pytest.fixture
def current_ticket_file(mock_project_root: Path, current_branch_name: str) -> Path:
    """Get the ticket path for the current branch name.

    Args:
        mock_project_root (Path): Root of the mock project.
        current_branch_name (str): Current branch under test.

    Returns:
        Path: Expected ticket file path.
    """
    project_name = get_project_name(project_root=mock_project_root)
    return mock_project_root.joinpath(
        "docs", "tickets", project_name, f"{current_branch_name}.rst"
    )


@pytest.fixture
def ticket_for_current_branch(
    current_ticket_file: Path, current_ticket_id: str, current_branch_name: str
) -> Path:
    """Write a ticket file matching the active branch name.

    Args:
        current_ticket_file (Path): Expected ticket file path.
        current_ticket_id (str): Current ticket id.
        current_branch_name (str): Current branch under test.

    Returns:
        Path: The written ticket file path.
    """
    current_ticket_file.parent.mkdir(parents=True, exist_ok=True)
    current_ticket_file.write_text(
        f"{current_ticket_id}: Mock Ticket\n"
        "====================\n"
        "\n"
        "Overview\n"
        "--------\n"
        f"Mock ticket file for branch `{current_branch_name}`.\n"
    )
    return current_ticket_file


@pytest.fixture
def dummy_feature_test(mock_project_root: Path, current_ticket_id: str) -> Path:
    """Write the required dummy feature test for process checks.

    Args:
        mock_project_root (Path): Root of the mock project.
        current_ticket_id (str): Current ticket id.

    Returns:
        Path: Path to the written dummy feature test file.
    """
    project_name = get_project_name(project_root=mock_project_root)
    feature_test_file = mock_project_root.joinpath(
        "build_support",
        "test",
        "feature_tests",
        f"test_{current_ticket_id}_{project_name}.py",
    )
    feature_test_file.write_text("def test_dummy() -> None:\n    assert True\n")
    return feature_test_file


@pytest.fixture
def mock_new_branch(
    mock_remote_git_repo: Repo, mock_lightweight_project: Repo, current_branch_name: str
) -> Head:
    """Create and check out a new feature branch on the mock project.

    Args:
        mock_remote_git_repo (Repo): The mock bare remote repo.
        mock_lightweight_project (Repo): The mock project repo.
        current_branch_name (str): Branch name used for this test case.

    Returns:
        Head: The newly created and checked-out branch.
    """
    mock_remote_git_repo.create_head(current_branch_name)
    mock_lightweight_project.remote().fetch()
    mock_lightweight_project.git.checkout(current_branch_name)
    return mock_lightweight_project.active_branch
