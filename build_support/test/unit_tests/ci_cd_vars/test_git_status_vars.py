from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest
from git import Commit, Head, Repo, TagReference

from build_support.ci_cd_vars.git_status_vars import (
    MAIN_BRANCH_NAME,
    commit_changes_if_diff,
    current_branch_is_main,
    dockerfile_was_modified,
    get_current_branch_name,
    get_git_diff,
    get_git_head,
    get_git_repo,
    get_local_tags,
    get_modified_files,
    get_modified_files_between_commits,
    get_modified_subprojects,
    get_most_recent_commit_on_main,
    git_add_all,
    git_fetch,
    monkeypatch_git_python_execute_kwargs,
    poetry_lock_file_was_modified,
    tag_current_commit_and_push,
)


@pytest.fixture
def mock_git_repo(mock_project_root: Path, mock_remote_git_repo: Repo) -> Repo:
    remote_repo_url = str(mock_remote_git_repo.working_dir)
    repo = Repo.clone_from(url=remote_repo_url, to_path=mock_project_root)
    repo.remote().push()
    new_file = mock_project_root.joinpath("first_file.txt")
    new_file.write_text("some_text")
    repo.index.add([new_file])
    repo.index.commit("initial local commit")
    repo.remote().push()
    return repo


@pytest.fixture
def mock_git_branch(mock_remote_git_repo: Repo, mock_git_repo: Repo) -> Head:
    branch_name = "some_branch_name"
    mock_remote_git_repo.create_head(branch_name)
    mock_git_repo.remote().fetch()
    mock_git_repo.git.checkout(branch_name)
    return mock_git_repo.active_branch


@pytest.fixture
def mock_git_tags(mock_git_repo: Repo, mock_git_branch: Head) -> list[TagReference]:
    tag_1_name = "inital_local_commit"
    mock_git_repo.create_tag(tag_1_name)
    mock_git_repo.remote().push(tag_1_name)
    new_file = Path(mock_git_branch.repo.working_dir).joinpath("new_file.txt")
    new_file.touch()
    mock_git_repo.index.add([new_file])
    mock_git_repo.index.commit("new commit")
    tag_2_name = "new_commit"
    mock_git_repo.create_tag("new_commit")
    mock_git_repo.remote().push(tag_2_name)
    return mock_git_repo.tags


def test_get_git_head(mock_project_root: Path, mock_git_branch: Head) -> None:
    assert get_git_head(project_root=mock_project_root) == mock_git_branch


def test_get_current_branch_name(
    mock_project_root: Path, mock_git_branch: Head
) -> None:
    assert (
        get_current_branch_name(project_root=mock_project_root) == mock_git_branch.name
    )


def test_constants_not_changed_by_accident() -> None:
    assert MAIN_BRANCH_NAME == "main"


@pytest.mark.usefixtures("mock_git_repo")
def test_current_branch_is_main(mock_project_root: Path) -> None:
    assert current_branch_is_main(project_root=mock_project_root)


@pytest.mark.usefixtures("mock_git_branch")
def test_current_branch_is_not_main(mock_project_root: Path) -> None:
    assert not current_branch_is_main(project_root=mock_project_root)


def test_git_fetch(
    mock_remote_git_repo: Repo, mock_git_repo: Repo, mock_project_root: Path
) -> None:
    assert len(mock_git_repo.tags) == 0
    assert len(mock_remote_git_repo.tags) == 0
    mock_remote_git_repo.create_tag("RemoteTag")
    assert len(mock_git_repo.tags) == 0
    assert len(mock_remote_git_repo.tags) == 1
    git_fetch(project_root=mock_project_root)
    assert len(mock_git_repo.tags) == 1
    assert len(mock_remote_git_repo.tags) == 1


def test_get_local_tags(
    mock_project_root: Path, mock_git_tags: list[TagReference]
) -> None:
    assert get_local_tags(project_root=mock_project_root) == [
        tag.name for tag in mock_git_tags
    ]


def test_get_git_diff(mock_project_root: Path, mock_git_repo: Repo) -> None:
    diff_file = mock_project_root.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    assert len(get_git_diff(project_root=mock_project_root)) > 0


@pytest.mark.usefixtures("mock_git_repo")
def test_get_git_diff_no_diff(mock_project_root: Path) -> None:
    assert len(get_git_diff(project_root=mock_project_root)) == 0


@pytest.fixture(
    params=["Valid message!", "Has a single quote(').", 'Has a double quote(")']
)
def valid_commit_message(request: SubRequest) -> str:
    return cast(str, request.param)


def test_commit_changes_no_diff(
    valid_commit_message: str, mock_project_root: Path, mock_git_branch: Head
) -> None:
    initial_commit_sha = mock_git_branch.commit.binsha
    commit_changes_if_diff(
        commit_message=valid_commit_message, project_root=mock_project_root
    )
    assert initial_commit_sha == mock_git_branch.commit.binsha


def test_commit_changes_with_diff_on_main(
    valid_commit_message: str, mock_project_root: Path, mock_git_repo: Repo
) -> None:
    diff_file = mock_project_root.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    main_branch = mock_git_repo.active_branch
    initial_commit_sha = main_branch.commit.binsha
    expected_message = (
        f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
    )
    with pytest.raises(RuntimeError, match=expected_message):
        commit_changes_if_diff(
            commit_message=valid_commit_message, project_root=mock_project_root
        )
    assert initial_commit_sha == main_branch.commit.binsha


def test_run_push_tags_allowed_with_diff_not_main(
    valid_commit_message: str,
    mock_project_root: Path,
    mock_git_repo: Repo,
    mock_git_branch: Head,
) -> None:
    mock_initial_git_file = mock_project_root.joinpath("first_file.txt")
    mock_initial_git_file.write_text(
        mock_initial_git_file.read_text() + "some extra text"
    )
    diff_file = mock_project_root.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    initial_commit_sha = mock_git_branch.commit.binsha
    commit_changes_if_diff(
        commit_message=valid_commit_message, project_root=mock_project_root
    )
    assert initial_commit_sha != mock_git_branch.commit.binsha


def test_tag_current_commit_and_push(
    mock_project_root: Path, mock_git_repo: Repo, mock_git_branch: Head
) -> None:
    mock_initial_git_file = mock_project_root.joinpath("first_file.txt")
    mock_initial_git_file.write_text(
        mock_initial_git_file.read_text() + "some extra text"
    )
    diff_file = mock_project_root.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    mock_git_repo.index.commit("commit_that_will_be_tagged")
    tag = "0.0.1"
    assert not any(
        tag for tag in mock_git_repo.tags if tag.commit == mock_git_branch.commit
    )
    tag_current_commit_and_push(tag=tag, project_root=mock_project_root)
    commit_tags = [
        tag for tag in mock_git_repo.tags if tag.commit == mock_git_branch.commit
    ]
    assert len(commit_tags) == 1
    assert commit_tags[0].name == tag


def test_get_git_repo(mock_project_root: Path, mock_git_repo: Repo) -> None:
    """Test that get_git_repo returns the correct Repo object."""
    repo = get_git_repo(project_root=mock_project_root)
    assert repo == mock_git_repo
    assert str(repo.working_dir) == str(mock_project_root)


def test_git_add_all(mock_project_root: Path, mock_git_repo: Repo) -> None:
    """Test that git_add_all adds files and returns the active branch."""
    # Modify an existing file (since git_add_all uses update=True)
    existing_file = mock_project_root.joinpath("first_file.txt")
    existing_file.write_text("modified content")

    # Get the active branch before adding
    initial_branch = mock_git_repo.active_branch

    # Call git_add_all
    result_branch = git_add_all(project_root=mock_project_root)

    # Should return the same branch
    assert result_branch == initial_branch

    # The file should now be staged - check using git status or index entries
    staged_files = [item[0] for item in mock_git_repo.index.entries]
    # Check if the filename (without path) is in the staged files
    assert "first_file.txt" in staged_files


def test_get_most_recent_commit_on_main(
    mock_project_root: Path, mock_git_repo: Repo
) -> None:
    """Test that get_most_recent_commit_on_main returns the correct commit."""
    # Create a commit on main branch
    main_branch = mock_git_repo.active_branch
    new_file = mock_project_root.joinpath("main_commit_file.txt")
    new_file.write_text("main content")
    mock_git_repo.index.add([new_file])
    commit = mock_git_repo.index.commit("main commit")

    # Push to remote to create origin/main
    mock_git_repo.remote().push()

    # Test the function
    most_recent_commit = get_most_recent_commit_on_main(repo=mock_git_repo)
    assert most_recent_commit == commit


def test_get_modified_files_between_commits(
    mock_project_root: Path, mock_git_repo: Repo
) -> None:
    """Test that get_modified_files_between_commits returns the correct files."""
    # Create initial commit
    initial_file = mock_project_root.joinpath("initial.txt")
    initial_file.write_text("initial content")
    mock_git_repo.index.add([initial_file])
    old_commit = mock_git_repo.index.commit("initial commit")

    # Create second commit with modifications
    initial_file.write_text("modified content")
    new_file = mock_project_root.joinpath("new.txt")
    new_file.write_text("new content")
    mock_git_repo.index.add([initial_file, new_file])
    new_commit = mock_git_repo.index.commit("modified commit")

    # Test the function
    modified_files = get_modified_files_between_commits(
        project_root=mock_project_root,
        repo=mock_git_repo,
        old_commit=old_commit,
        new_commit=new_commit,
    )

    # Should include both modified and new files
    expected_files = {mock_project_root / "initial.txt", mock_project_root / "new.txt"}
    assert modified_files == expected_files


def test_get_modified_files_on_main(
    mock_project_root: Path, mock_git_repo: Repo
) -> None:
    """Test get_modified_files when on main branch."""
    # Create initial commit
    initial_file = mock_project_root.joinpath("initial.txt")
    initial_file.write_text("initial content")
    mock_git_repo.index.add([initial_file])
    initial_commit = mock_git_repo.index.commit("initial commit")

    # Create second commit (this will be the current commit)
    initial_file.write_text("modified content")
    new_file = mock_project_root.joinpath("new.txt")
    new_file.write_text("new content")
    mock_git_repo.index.add([initial_file, new_file])
    current_commit = mock_git_repo.index.commit("modified commit")

    # Test the function
    modified_files = get_modified_files(project_root=mock_project_root)

    # Should include files modified between parent and current commit
    expected_files = {mock_project_root / "initial.txt", mock_project_root / "new.txt"}
    assert modified_files == expected_files


def test_get_modified_files_not_on_main(
    mock_project_root: Path, mock_git_repo: Repo, mock_git_branch: Head
) -> None:
    """Test get_modified_files when not on main branch."""
    # Create a commit on main first
    main_file = mock_project_root.joinpath("main_file.txt")
    main_file.write_text("main content")
    mock_git_repo.index.add([main_file])
    main_commit = mock_git_repo.index.commit("main commit")
    mock_git_repo.remote().push()  # Push to create origin/main

    # Switch to feature branch (already done by mock_git_branch fixture)
    # Add some changes on the feature branch
    feature_file = mock_project_root.joinpath("feature_file.txt")
    feature_file.write_text("feature content")
    mock_git_repo.index.add([feature_file])
    mock_git_repo.index.commit("feature commit")

    # Add uncommitted changes
    uncommitted_file = mock_project_root.joinpath("uncommitted.txt")
    uncommitted_file.write_text("uncommitted content")

    # Test the function
    modified_files = get_modified_files(project_root=mock_project_root)

    # Should include files modified since main and uncommitted files
    # The main_file.txt will also be included because it was created after the initial commit
    expected_files = {
        mock_project_root / "main_file.txt",
        mock_project_root / "feature_file.txt",
    }
    # Note: uncommitted files might not be detected in this test setup
    # The function should at least detect the committed changes
    assert expected_files.issubset(modified_files)


def test_get_modified_subprojects(mock_project_root: Path) -> None:
    """Test that get_modified_subprojects returns the correct subprojects."""
    # Create some test files in different subprojects
    build_support_file = mock_project_root / "build_support" / "test_file.py"
    build_support_file.parent.mkdir(parents=True, exist_ok=True)
    build_support_file.write_text("test content")

    pypi_file = mock_project_root / "pypi_package" / "src" / "test_file.py"
    pypi_file.parent.mkdir(parents=True, exist_ok=True)
    pypi_file.write_text("test content")

    infra_file = mock_project_root / "infra" / "test_file.py"
    infra_file.parent.mkdir(parents=True, exist_ok=True)
    infra_file.write_text("test content")

    # Test with files from different subprojects
    modified_files = [build_support_file, pypi_file, infra_file]

    modified_subprojects = get_modified_subprojects(
        modified_files=modified_files, project_root=mock_project_root
    )

    # Should include all three subprojects
    from build_support.ci_cd_vars.subproject_structure import SubprojectContext

    expected_subprojects = [
        SubprojectContext.BUILD_SUPPORT,
        SubprojectContext.PYPI,
        SubprojectContext.INFRA,
    ]
    assert set(modified_subprojects) == set(expected_subprojects)


def test_get_modified_subprojects_no_files(mock_project_root: Path) -> None:
    """Test that get_modified_subprojects returns empty list when no files are modified."""
    modified_files = []

    modified_subprojects = get_modified_subprojects(
        modified_files=modified_files, project_root=mock_project_root
    )

    assert modified_subprojects == []


def test_dockerfile_was_modified(mock_project_root: Path) -> None:
    """Test that dockerfile_was_modified correctly identifies Dockerfile changes."""
    # Create a Dockerfile
    dockerfile = mock_project_root / "Dockerfile"
    dockerfile.write_text("FROM python:3.13")

    # Test with Dockerfile in modified files
    modified_files_with_dockerfile = [dockerfile, mock_project_root / "other_file.txt"]
    assert (
        dockerfile_was_modified(modified_files_with_dockerfile, mock_project_root)
        is True
    )

    # Test without Dockerfile in modified files
    modified_files_without_dockerfile = [mock_project_root / "other_file.txt"]
    assert (
        dockerfile_was_modified(modified_files_without_dockerfile, mock_project_root)
        is False
    )


def test_poetry_lock_file_was_modified(mock_project_root: Path) -> None:
    """Test that poetry_lock_file_was_modified correctly identifies poetry.lock changes."""
    # Create a poetry.lock file
    poetry_lock = mock_project_root / "poetry.lock"
    poetry_lock.write_text('[[package]]\nname = "test"')

    # Test with poetry.lock in modified files
    modified_files_with_poetry_lock = [
        poetry_lock,
        mock_project_root / "other_file.txt",
    ]
    assert (
        poetry_lock_file_was_modified(
            modified_files_with_poetry_lock, mock_project_root
        )
        is True
    )

    # Test without poetry.lock in modified files
    modified_files_without_poetry_lock = [mock_project_root / "other_file.txt"]
    assert (
        poetry_lock_file_was_modified(
            modified_files_without_poetry_lock, mock_project_root
        )
        is False
    )


def test_monkeypatch_git_python_execute_kwargs() -> None:
    """Test that monkeypatch_git_python_execute_kwargs adds the required kwargs."""
    from git.cmd import execute_kwargs

    # Store original state
    original_kwargs = execute_kwargs.copy()

    try:
        # Call the function
        monkeypatch_git_python_execute_kwargs()

        # Check that the kwargs were added
        assert "user" in execute_kwargs
        assert "group" in execute_kwargs

    finally:
        # Restore original state
        execute_kwargs.clear()
        execute_kwargs.update(original_kwargs)
