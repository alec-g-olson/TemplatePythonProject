"""Collection of all functions and variable that report git information.

Attributes:
    | MAIN_BRANCH_NAME: The name of the main branch for this repo.
"""

from pathlib import Path

from git import DiffIndex, Head, Repo


def get_git_repo(project_root: Path) -> Repo:
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


def get_local_tags(project_root: Path) -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run `git fetch` before this function.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: The list of all tags on the local version of your git repo.
    """
    return [tag.name for tag in get_git_repo(project_root=project_root).tags]


def get_git_diff(project_root: Path) -> DiffIndex:
    """Gets the result of `git diff`.  If not empty, there are unstaged changes.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The results of running `git diff`.
    """
    return get_git_head(project_root=project_root).commit.diff()


def commit_changes_if_diff(commit_message: str, project_root: Path) -> None:
    """Commits changes to the active branch if there are any uncommitted changes.

    Args:
        commit_message (str): The message that will be put on the commit if the commit
            is successful.
        project_root (Path): Path to this project's root.

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
        repo.git.add(update=True)
        repo.index.commit(commit_message)
        repo.remote().push()


def tag_current_commit_and_push(tag: str, project_root: Path) -> None:
    """Tags the working commit with the supplied tag, and pushes to remote.

    Args:
        tag (str): The message that the working commit will be tagged with.
        project_root (Path): Path to this project's root.

    Returns:
        None
    """
    repo = get_git_repo(project_root=project_root)
    repo.create_tag(tag)
    repo.remote().push(tag)
