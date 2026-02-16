"""Collection of all functions and variable that report project level settings.

Attributes:
    | ALLOWED_VERSION_REGEX: A regex for allowed version numbers for this project.
"""

import re
import tomllib
from pathlib import Path

from tomlkit import TOMLDocument, parse

from build_support.ci_cd_vars.project_structure import (
    get_poetry_lock_file,
    get_pyproject_toml,
)

########################################
# Settings contained in pyproject.toml
########################################


def get_pyproject_toml_data(project_root: Path) -> TOMLDocument:
    """Get a TOMLDocument with the contents of the pyproject.toml in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        TOMLDocument: A parsed TOMLDocument that preserves structure and formatting.
    """
    return parse(get_pyproject_toml(project_root=project_root).read_text())


ALLOWED_VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+(-dev\.\d+)?$")


def get_project_version(project_root: Path) -> str:
    """Gets the project version from the pyproject.toml in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The current version of the project.
    """
    pyproject_data = get_pyproject_toml_data(project_root=project_root)
    version_str: str
    version_str = pyproject_data["tool"]["poetry"][  # type: ignore[index, assignment]
        "version"
    ]
    if not ALLOWED_VERSION_REGEX.match(version_str):
        msg = (
            "Project version in pyproject.toml must match the regex "
            f"'{ALLOWED_VERSION_REGEX.pattern}', found '{version_str}'."
        )
        raise ValueError(msg)
    return "v" + version_str


def is_dev_project_version(project_version: str) -> bool:
    """Determines if the current project version is a dev version.

    Args:
        project_version (str): A project version string.

    Returns:
        bool: Is the project version provided a dev version.
    """
    return "dev" in project_version


def is_prod_project_version(project_version: str) -> bool:
    """Determines if the current project version is a production version.

    Args:
        project_version (str): A project version string.

    Returns:
        bool: Is the project version provided a production version.
    """
    return "dev" not in project_version


def get_project_name(project_root: Path) -> str:
    """Gets the project name from the pyproject.toml in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The name of the project.
    """
    pyproject_data = get_pyproject_toml_data(project_root=project_root)
    return pyproject_data["tool"]["poetry"]["name"]  # type: ignore[index, return-value]


########################################
# Settings pulled from poetry.lock
########################################


def get_pulumi_version(project_root: Path) -> str:
    """Get the infra version in the poetry lock file.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The infra version in the poetry lock file.
    """
    lock_file = get_poetry_lock_file(project_root=project_root)
    lock_data = tomllib.loads(lock_file.read_text())
    for package in lock_data["package"]:
        if package["name"] == "pulumi":
            return str(package["version"])
    msg = (
        "poetry.lock does not have a pulumi package installed, "
        "or is no longer a toml format."
    )
    raise ValueError(msg)
