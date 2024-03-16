"""Collection of all functions and variable that report git information.

Attributes:
    | MAIN_BRANCH_NAME: The name of the main branch for this repo.
"""

from build_support.process_runner import (
    concatenate_args,
    get_output_of_process,
    run_process,
)


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


def commit_changes_if_diff(
    commit_message_no_quotes: str,
    local_user_uid: int = 0,
    local_user_gid: int = 0,
) -> None:
    """Gets the branch that is currently checked out.

    Args:
        commit_message_no_quotes (str): The message that will be put on the commit
            if the commit is successful.  Cannot contain double quotes.
        local_user_uid (int): The local user's users id, used when tasks need to be
            run by the local user.
        local_user_gid (int): The local user's group id, used when tasks need to be
            run by the local user.

    Returns:
        str: The name of the git branch that is currently checked out.
    """
    if '"' in commit_message_no_quotes:
        msg = (
            "Commit message is not allowed to have double quotes. "
            f"commit_message_no_quotes='{commit_message_no_quotes}'"
        )
        raise ValueError(msg)
    current_diff = get_git_diff()
    if current_diff:
        if current_branch_is_main(
            current_branch=get_current_branch(
                local_user_uid=local_user_uid,
                local_user_gid=local_user_gid,
            )
        ):
            msg = (
                f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
            )
            raise RuntimeError(msg)
        run_process(
            args=concatenate_args(args=["git", "add", "-u"]),
            user_uid=local_user_uid,
            user_gid=local_user_gid,
        )
        run_process(
            args=concatenate_args(
                args=[
                    "git",
                    "commit",
                    "-m",
                    f'"{commit_message_no_quotes}"',
                ],
            ),
            user_uid=local_user_uid,
            user_gid=local_user_gid,
        )
        run_process(
            args=concatenate_args(args=["git", "push"]),
            user_uid=local_user_uid,
            user_gid=local_user_gid,
        )
