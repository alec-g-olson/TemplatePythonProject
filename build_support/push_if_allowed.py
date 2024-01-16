"""A helper script to push the artifact if allowed based on version number."""
import json
import tomllib
from pathlib import Path
from subprocess import run

PROJECT_ROOT_DIR: Path = Path(__file__).parent.parent


def get_current_version() -> str:
    """Gets the current version of the artifact."""
    toml_data = tomllib.loads(PROJECT_ROOT_DIR.joinpath("pyproject.toml").read_text())
    return "v" + toml_data["tool"]["poetry"]["version"]


def get_current_branch() -> str:
    """Gets the current branch."""
    json_data = json.loads(
        PROJECT_ROOT_DIR.joinpath("build", "git_info.json").read_text()
    )
    return json_data["branch"]


def allowed_to_push() -> bool:
    """Determines if the version is appropriate for the current branch."""
    branch = get_current_branch()
    version = get_current_version()
    return (branch == "main") ^ ("dev" in version)


def push_tags() -> None:
    """Tags and pushes the tag for the current commit."""
    run(args=["git", "tag", get_current_version()])
    run(args=["git", "push", "--tags"])


def push_artifact() -> None:
    """Pushes the artifact."""


if __name__ == "__main__":
    if allowed_to_push():
        exit(0)
    else:
        exit(1)
