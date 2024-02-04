"""Collection of all functions and variable that report git information."""
from dag_engine import get_output_of_process


def get_current_branch() -> str:
    """Gets the branch that is currently checked out."""
    return get_output_of_process(
        args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
    )


def get_local_tags() -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run "git fetch" before this function.
    """
    return get_output_of_process(args=["git", "tag"], silent=True).split("\n")
