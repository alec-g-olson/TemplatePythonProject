from pathlib import Path

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
)


@pytest.fixture()
def mock_remote_git_folder(mock_project_root: Path) -> Path:
    remote_folder = mock_project_root.joinpath("remote_repo")
    remote_folder.mkdir()
    return remote_folder


@pytest.fixture()
def mock_git_folder(mock_project_root: Path) -> Path:
    local_folder = mock_project_root.joinpath("local_repo")
    local_folder.mkdir()
    return local_folder


@pytest.fixture()
def mock_remote_git_repo(mock_remote_git_folder: Path) -> Repo:
    repo = Repo.init(path=mock_remote_git_folder, bare=True, initial_branch=MAIN_BRANCH_NAME)
    repo.index.commit("initial remote commit")
    return repo


@pytest.fixture()
def mock_git_repo(mock_git_folder: Path, mock_remote_git_folder: Path, mock_remote_git_repo: Repo) -> Repo:
    remote_repo_url = str(mock_remote_git_folder)
    repo = Repo.clone_from(url=remote_repo_url, to_path=mock_git_folder)
    repo.remote().push()
    new_file = mock_git_folder.joinpath("first_file.txt")
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
def mock_git_tags(
    mock_git_folder: Path, mock_git_repo: Repo, mock_git_branch: Head
) -> list[TagReference]:
    tag_1_name = "inital_local_commit"
    mock_git_repo.create_tag(tag_1_name)
    mock_git_repo.remote().push(tag_1_name)
    new_file = mock_git_folder.joinpath("new_file.txt")
    new_file.touch()
    mock_git_repo.index.add([new_file])
    mock_git_repo.index.commit("new commit")
    tag_2_name = "new_commit"
    mock_git_repo.create_tag("new_commit")
    mock_git_repo.remote().push(tag_2_name)
    return mock_git_repo.tags


def test_get_git_head(mock_git_folder: Path, mock_git_branch: Head) -> None:
    assert get_git_head(project_root=mock_git_folder) == mock_git_branch


def test_get_current_branch_name(
    mock_git_folder: Path, mock_git_branch: Head
) -> None:
    assert (
        get_current_branch_name(project_root=mock_git_folder) == mock_git_branch.name
    )


def test_constants_not_changed_by_accident() -> None:
    assert MAIN_BRANCH_NAME == "main"


@pytest.mark.usefixtures("mock_git_repo")
def test_current_branch_is_main(mock_git_folder: Path) -> None:
    assert current_branch_is_main(project_root=mock_git_folder)


@pytest.mark.usefixtures("mock_git_branch")
def test_current_branch_is_not_main(mock_git_folder: Path) -> None:
    assert not current_branch_is_main(project_root=mock_git_folder)


def test_get_local_tags(
    mock_git_folder: Path, mock_git_tags: list[TagReference]
) -> None:
    assert get_local_tags(project_root=mock_git_folder) == [
        tag.name for tag in mock_git_tags
    ]


@pytest.mark.usefixtures()
def test_get_git_diff(mock_git_folder: Path, mock_git_repo: Repo) -> None:
    diff_file = mock_git_folder.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    assert len(get_git_diff(project_root=mock_git_folder)) > 0


@pytest.mark.usefixtures("mock_git_repo")
def test_get_git_diff_no_diff(mock_git_folder: Path) -> None:
    assert len(get_git_diff(project_root=mock_git_folder)) == 0


@pytest.fixture(
    params=["Valid message!", "Has a single quote(').", 'Has a double quote(")']
)
def valid_commit_message(request: SubRequest) -> str:
    return request.param


def test_commit_changes_no_diff(
    valid_commit_message: str, mock_git_folder: Path, mock_git_branch: Head
) -> None:
    initial_commit_sha = mock_git_branch.commit.binsha
    commit_changes_if_diff(
        commit_message=valid_commit_message, project_root=mock_git_folder
    )
    assert initial_commit_sha == mock_git_branch.commit.binsha


def test_commit_changes_with_diff_on_main(
    valid_commit_message: str, mock_git_folder: Path, mock_git_repo: Repo
) -> None:
    diff_file = mock_git_folder.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    main_branch = mock_git_repo.active_branch
    initial_commit_sha = main_branch.commit.binsha
    expected_message = (
        f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
    )
    with pytest.raises(RuntimeError, match=expected_message):
        commit_changes_if_diff(
            commit_message=valid_commit_message, project_root=mock_git_folder
        )
    assert initial_commit_sha == main_branch.commit.binsha


def test_run_push_tags_allowed_with_diff_not_main(
    valid_commit_message: str,
    mock_git_folder: Path,
    mock_git_repo: Repo,
    mock_git_branch: Head,
) -> None:
    mock_initial_git_file = mock_git_folder.joinpath("first_file.txt")
    mock_initial_git_file.write_text(
        mock_initial_git_file.read_text() + "some extra text"
    )
    diff_file = mock_git_folder.joinpath("diff_file")
    diff_file.touch()
    mock_git_repo.index.add([diff_file])
    initial_commit_sha = mock_git_branch.commit.binsha
    commit_changes_if_diff(
        commit_message=valid_commit_message, project_root=mock_git_folder
    )
    assert initial_commit_sha != mock_git_branch.commit.binsha