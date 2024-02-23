"""Collection of all functions and variable that report project level settings.

Attributes:
    | ALLOWED_VERSION_REGEX: A regex for allowed version numbers for this project.
"""
import re
import tomllib
from pathlib import Path
from typing import Any

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_poetry_lock_file,
    get_pyproject_toml,
)

########################################
# Settings contained in pyproject.toml
########################################


def get_pyproject_toml_data(project_root: Path) -> dict[Any, Any]:
    """Get a dict with the contents of the pyproject.toml in a project."""
    return tomllib.loads(get_pyproject_toml(project_root=project_root).read_text())


ALLOWED_VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+(-dev\.\d+)?$")


def get_project_version(project_root: Path) -> str:
    """Gets the project version from the pyproject.toml in a project."""
    version_str = get_pyproject_toml_data(project_root=project_root)["tool"]["poetry"][
        "version"
    ]
    if not ALLOWED_VERSION_REGEX.match(version_str):
        allowed_regex_str = ALLOWED_VERSION_REGEX.pattern
        raise ValueError(
            "Project version in pyproject.toml must match the regex "
            f"'{allowed_regex_str}', found '{version_str}'."
        )
    return "v" + version_str


def is_dev_project_version(project_version: str) -> bool:
    """Determines if the current project version is a dev version."""
    return "dev" in project_version


def is_prod_project_version(project_version: str) -> bool:
    """Determines if the current project version is a production version."""
    return "dev" not in project_version


def get_project_name(project_root: Path) -> str:
    """Gets the project name from the pyproject.toml in a project."""
    return get_pyproject_toml_data(project_root=project_root)["tool"]["poetry"]["name"]


########################################
# Settings pulled from poetry.lock
########################################


def get_pulumi_version(project_root: Path) -> str:
    """Get the pulumi version in the poetry.lock file."""
    lock_file = get_poetry_lock_file(project_root=project_root)
    lock_data = tomllib.loads(lock_file.read_text())
    for package in lock_data["package"]:
        if package["name"] == "pulumi":
            return package["version"]
    raise ValueError(
        "poetry.lock does not have a pulumi package installed, "
        "or is no longer a toml format."
    )
