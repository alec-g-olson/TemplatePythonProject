"""Defines the top level project structure."""

from pathlib import Path


def maybe_build_dir(dir_to_build: Path) -> Path:
    """Builds a directory and returns its path.

    Args:
        dir_to_build (Path): Path to the directory we want to build if it is missing.
            Will builds parents as needed.

    Returns:
        Path: Path to the directory that was requested.
    """
    dir_to_build.mkdir(parents=True, exist_ok=True)
    return dir_to_build


########################################
# Top level files and folders
########################################


def get_pyproject_toml(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the pyproject.toml file in this project.
    """
    return project_root.joinpath("pyproject.toml")


def get_license_file(project_root: Path) -> Path:
    """Get a path to the LICENSE file in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the LICENSE file in this project.
    """
    return project_root.joinpath("LICENSE")


def get_poetry_lock_file(project_root: Path) -> Path:
    """Get a path to the poetry lock file in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the poetry lock file in this project.
    """
    return project_root.joinpath("poetry.lock")


def get_build_dir(project_root: Path) -> Path:
    """Gets the build directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build directory for this project.
    """
    return maybe_build_dir(dir_to_build=project_root.joinpath("build"))


def get_docs_dir(project_root: Path) -> Path:
    """Gets the docs directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the docs directory for this project.
    """
    return maybe_build_dir(dir_to_build=project_root.joinpath("docs"))


def get_dockerfile(project_root: Path) -> Path:
    """Gets the Dockerfile for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the Dockerfile for this project.
    """
    return project_root.joinpath("Dockerfile")
