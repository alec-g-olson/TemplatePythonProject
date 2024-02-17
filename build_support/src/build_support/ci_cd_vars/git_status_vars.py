"""Collection of all functions and variable that report git information."""
from build_support.dag_engine import get_output_of_process


def get_current_branch() -> str:
    """Gets the branch that is currently checked out."""
    return get_output_of_process(
        args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
    )


MAIN_BRANCH_NAME = "main"


def current_branch_is_main(current_branch: str) -> bool:
    """Determines if the branch currently checked out is main."""
    return current_branch == MAIN_BRANCH_NAME


def get_local_tags() -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run "git fetch" before this function.
    """
    return get_output_of_process(args=["git", "tag"], silent=True).split("\n")


def get_git_diff() -> str:
    """Gets the result of "git diff".  If not empty, there are unstaged changes."""
    return get_output_of_process(args=["git", "diff"], silent=True)
