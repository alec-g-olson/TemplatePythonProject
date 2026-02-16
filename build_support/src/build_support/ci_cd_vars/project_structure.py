"""Defines the structure and organization of top-level project folders and files.

This includes files like pyproject.toml, Dockerfile, README.md, and top-level
directories like build/, docs/, and test_scratch_folder/.
"""

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


def get_feature_test_scratch_folder(project_root: Path) -> Path:
    """Gets the directory that will be used as a scratch folder for feature tests.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the scratch folder for feature tests.
    """
    return maybe_build_dir(dir_to_build=project_root.joinpath("test_scratch_folder"))


def get_feature_test_log_name(project_root: Path, test_name: str) -> Path:
    """Gets the path to a log file for a feature test.

    Args:
        project_root (Path): Path to this project's root.
        test_name (str): Name of the test (will be sanitized for filename).

    Returns:
        Path: Path to the log file for the test in test_scratch_folder/test_logs/.
    """
    # Sanitize test name for use as filename
    safe_test_name = test_name.replace("[", "_").replace("]", "_").replace("::", "_")
    # Remove trailing underscores that may result from sanitization
    safe_test_name = safe_test_name.rstrip("_")
    log_dir = maybe_build_dir(
        dir_to_build=get_feature_test_scratch_folder(
            project_root=project_root
        ).joinpath("test_logs")
    )
    return log_dir.joinpath(f"{safe_test_name}.log")


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


def get_readme(project_root: Path) -> Path:
    """Gets the README for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the README for this project.
    """
    return project_root.joinpath("README.md")


def get_sphinx_conf_dir(project_root: Path) -> Path:
    """Gets the sphinx config file for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the sphinx config directory in this project.
    """
    return get_docs_dir(project_root=project_root).joinpath("sphinx_conf")


def get_new_project_settings(project_root: Path) -> Path:
    """Get a path to the new_project_settings.yaml file in this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the new_project_settings.yaml file in this project.
    """
    return project_root.joinpath("new_project_settings.yaml")


def get_test_resource_dir(test_file: Path) -> Path:
    """Return the resource directory for a given test file.

    Convention: a test file ``test_foo.py`` has resources in a sibling
    directory named ``test_foo_resources/``.

    Args:
        test_file (Path): Path to the test file.

    Returns:
        Path: Path to the test file's resource directory.
    """
    return test_file.parent / f"{test_file.stem}_resources"
