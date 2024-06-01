"""Collection of all functions and variable that report git information.

Attributes:
    | MAIN_BRANCH_NAME: The name of the main branch for this repo.
"""

from pathlib import Path
from typing import Iterable

from git import DiffIndex, FetchInfo, Head, Repo
from git.cmd import execute_kwargs
from git.diff import Diff


def get_git_repo(project_root: Path) -> Repo:
    """Gets a python representation of the project's git repo.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Repo: This project's git repo.
    """
    return Repo(project_root)


def get_git_head(project_root: Path) -> Head:
    """Gets the branch that is currently checked out.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Head: The active commit/branch of the git repo.
    """
    return get_git_repo(project_root=project_root).active_branch


def get_current_branch_name(project_root: Path) -> str:
    """Gets the branch that is currently checked out.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The name of the active commit/branch of the git repo.
    """
    return get_git_head(project_root=project_root).name


MAIN_BRANCH_NAME = "main"


def current_branch_is_main(project_root: Path) -> bool:
    """Determines if the branch currently checked out is main.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        bool: Is the current branch the main branch.
    """
    return get_current_branch_name(project_root=project_root) == MAIN_BRANCH_NAME


def monkeypatch_git_python_execute_kwargs() -> None:
    """Monkey patches some execute kwargs, so we can run git as a local user in docker.

    Returns:
        None
    """
    execute_kwargs.add("user")
    execute_kwargs.add("group")


def git_fetch(
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> Iterable[FetchInfo]:
    """Fetches from the remote repo.

    Args:
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        Iterable[FetchInfo]: The name of the active commit/branch of the git repo.
    """
    monkeypatch_git_python_execute_kwargs()
    return (
        get_git_repo(project_root=project_root)
        .remote()
        .fetch(user=local_uid, group=local_gid, env=local_user_env)
    )


def get_local_tags(project_root: Path) -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run `git fetch` before this function.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: The list of all tags on the local version of your git repo.
    """
    return [tag.name for tag in get_git_repo(project_root=project_root).tags]


def git_add_all(project_root: Path) -> Head:
    """Adds all files te the current git index.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Head: The active commit/branch of the git repo.
    """
    repo = get_git_repo(project_root=project_root)
    repo.git.add(update=True)
    return repo.active_branch


def get_git_diff(project_root: Path) -> DiffIndex[Diff]:
    """Gets the result of `git diff`.  If not empty, there are unstaged changes.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The results of running `git diff`.
    """
    return git_add_all(project_root=project_root).commit.diff()  # type: ignore[no-any-return]


def commit_changes_if_diff(
    commit_message: str,
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> None:
    """Commits changes to the active branch if there are any uncommitted changes.

    Args:
        commit_message (str): The message that will be put on the commit if the commit
            is successful.
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        None
    """
    current_diff = get_git_diff(project_root=project_root)
    if current_diff:
        if current_branch_is_main(project_root=project_root):
            msg = (
                f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
            )
            raise RuntimeError(msg)
        repo = get_git_repo(project_root=project_root)
        git_add_all(project_root=project_root)
        repo.index.commit(commit_message)
        monkeypatch_git_python_execute_kwargs()
        repo.remote().push(user=local_uid, group=local_gid, env=local_user_env)


def tag_current_commit_and_push(
    tag: str,
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> None:
    """Tags the working commit with the supplied tag, and pushes to remote.

    Args:
        tag (str): The message that the working commit will be tagged with.
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        None
    """
    repo = get_git_repo(project_root=project_root)
    repo.create_tag(tag)
    monkeypatch_git_python_execute_kwargs()
    repo.remote().push(tag, user=local_uid, group=local_gid, env=local_user_env)
