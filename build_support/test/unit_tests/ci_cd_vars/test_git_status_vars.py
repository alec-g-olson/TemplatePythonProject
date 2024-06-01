from pathlib import Path
from typing import cast

import pytest
from _pytest.fixtures import SubRequest
from git import Head, Repo, TagReference

from build_support.ci_cd_vars.git_status_vars import (
    MAIN_BRANCH_NAME,
    commit_changes_if_diff,
    current_branch_is_main,
    get_current_branch_name,
    get_git_diff,
    get_git_head,
    get_local_tags,
    git_fetch,
    tag_current_commit_and_push,
)


@pytest.fixture()
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


@pytest.fixture()
def mock_git_branch(mock_remote_git_repo: Repo, mock_git_repo: Repo) -> Head:
    branch_name = "some_branch_name"
    mock_remote_git_repo.create_head(branch_name)
    mock_git_repo.remote().fetch()
    mock_git_repo.git.checkout(branch_name)
    return mock_git_repo.active_branch


@pytest.fixture()
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
