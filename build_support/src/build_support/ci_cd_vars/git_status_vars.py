"""Collection of all functions and variable that report git information.

Attributes:
    | MAIN_BRANCH_NAME: The name of the main branch for this repo.
"""
from build_support.dag_engine import get_output_of_process


def get_current_branch(
    local_user_uid: int = 0,
    local_user_gid: int = 0,
) -> str:
    """Gets the branch that is currently checked out.

    Args:
        local_user_uid (int): The local user's users id, used when tasks need to be
            run by the local user.
        local_user_gid (int): The local user's group id, used when tasks need to be
            run by the local user.

    Returns:
        str: The name of the git branch that is currently checked out.
    """
    return get_output_of_process(
        args=["git", "rev-parse", "--abbrev-ref", "HEAD"],
        user_uid=local_user_uid,
        user_gid=local_user_gid,
        silent=True,
    )


MAIN_BRANCH_NAME = "main"


def current_branch_is_main(current_branch: str) -> bool:
    """Determines if the branch currently checked out is main.

    Args:
        current_branch (str): The name of the current branch.

    Returns:
        bool: Is the current branch the main branch.
    """
    return current_branch == MAIN_BRANCH_NAME


def get_local_tags(
    local_user_uid: int = 0,
    local_user_gid: int = 0,
) -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run `git fetch` before this function.

    Args:
        local_user_uid (int): The local user's users id, used when tasks need to be
            run by the local user.
        local_user_gid (int): The local user's group id, used when tasks need to be
            run by the local user.

    Returns:
        list[str]: The list of all tags on the local version of your git repo.
    """
    return get_output_of_process(
        args=["git", "tag"],
        user_uid=local_user_uid,
        user_gid=local_user_gid,
        silent=True,
    ).split("\n")


def get_git_diff() -> str:
    """Gets the result of `git diff`.  If not empty, there are unstaged changes.

    Returns:
        str: The results of running `git diff`.
    """
    return get_output_of_process(args=["git", "diff"], silent=True)
