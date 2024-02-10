"""Collection of all file and folder path functions and variables."""
from enum import Enum
from pathlib import Path

from dag_engine import concatenate_args


def maybe_build_dir(dir_to_build: Path) -> Path:
    """Builds a directory and returns it's path."""
    dir_to_build.mkdir(parents=True, exist_ok=True)
    return dir_to_build


########################################
# Top level files and folders
########################################


def get_pyproject_toml(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project."""
    return project_root.joinpath("pyproject.toml")


def get_license_file(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project."""
    return project_root.joinpath("LICENSE")


def get_poetry_lock_file(project_root: Path) -> Path:
    """Get a path to the poetry.lock file in a project."""
    return project_root.joinpath("poetry.lock")


def get_build_dir(project_root: Path) -> Path:
    """Gets the build dir for the project."""
    return maybe_build_dir(dir_to_build=project_root.joinpath("build"))


def get_build_support_dir(project_root: Path) -> Path:
    """Gets the build_support dir for the project."""
    return project_root.joinpath("build_support")


def get_dockerfile(project_root: Path) -> Path:
    """Gets the Dockerfile for the project."""
    return project_root.joinpath("Dockerfile")


def get_pypi_dir(project_root: Path) -> Path:
    """Gets the PyPi pulumi dir for the project."""
    return project_root.joinpath("pypi_package")


def get_pulumi_dir(project_root: Path) -> Path:
    """Gets the PyPi pulumi dir for the project."""
    return project_root.joinpath("pulumi")


########################################
# Files and folders contained in build_support
########################################


def get_new_project_settings(project_root: Path) -> Path:
    """Get a path to the project_settings.yaml in a project."""
    return get_build_support_dir(project_root=project_root).joinpath(
        "project_settings.yaml"
    )


def get_build_support_src_dir(project_root: Path) -> Path:
    """Gets the build_src dir for the project."""
    return get_build_support_dir(project_root=project_root).joinpath("build_src")


def get_build_support_test_dir(project_root: Path) -> Path:
    """Gets the build_src dir for the project."""
    return get_build_support_dir(project_root=project_root).joinpath("build_test")


def get_build_support_src_and_test(project_root: Path) -> list[str]:
    """Gets both the build_src and build_test dir for the project."""
    return concatenate_args(
        args=[
            get_build_support_src_dir(project_root=project_root),
            get_build_support_test_dir(project_root=project_root),
        ]
    )


########################################
# Files and folders contained in pulumi
########################################


########################################
# Files and folder contained in pypi_package
########################################


def get_pypi_src_dir(project_root: Path) -> Path:
    """Gets the PyPi src dir for the project."""
    return get_pypi_dir(project_root=project_root).joinpath("src")


def get_pypi_test_dir(project_root: Path) -> Path:
    """Gets the PyPi test dir for the project."""
    return get_pypi_dir(project_root=project_root).joinpath("test")


def get_pypi_src_and_test(project_root: Path) -> list[str]:
    """Gets both the PyPi src and test dir for the project."""
    return concatenate_args(
        args=[
            get_pypi_src_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
        ]
    )


########################################
# Files and folders used during build process
########################################


def get_dist_dir(project_root: Path) -> Path:
    """Gets the dir where the pypi distribution will be located for the project."""
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("dist")
    )


def get_build_reports_dir(project_root: Path) -> Path:
    """Gets the dir that will contain the projects reports."""
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("reports")
    )


def get_license_templates_dir(project_root: Path) -> Path:
    """Gets the dir that will contain license templates used in building a new project."""
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath(
            "license_templates"
        )
    )


def get_git_info_yaml(project_root: Path) -> Path:
    """Gets the location of the git_info.json for the project."""
    return get_build_dir(project_root=project_root).joinpath("git_info.yaml")


def get_temp_dist_dir(project_root: Path) -> Path:
    """Gets the temporary dist dir for the project."""
    return maybe_build_dir(dir_to_build=project_root.joinpath("dist"))


########################################
# Files and folder collections that span domains
########################################


def get_all_non_pulumi_python_folders(project_root: Path) -> list[str]:
    """Gets all the non-pulumi python folders in the project."""
    return concatenate_args(
        args=[
            get_build_support_src_and_test(project_root=project_root),
            get_pypi_src_and_test(project_root=project_root),
        ]
    )


def get_all_python_folders(project_root: Path) -> list[str]:
    """Gets all the python folders in the project."""
    return concatenate_args(
        args=[
            get_all_non_pulumi_python_folders(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
        ]
    )


def get_all_src_folders(project_root: Path) -> list[str]:
    """Gets all the python src folders in the project."""
    return concatenate_args(
        args=[
            get_build_support_src_dir(project_root=project_root),
            get_pypi_src_dir(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
        ]
    )


def get_all_test_folders(project_root: Path) -> list[str]:
    """Gets all the python test folders in the project."""
    return concatenate_args(
        args=[
            get_build_support_test_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
        ]
    )


########################################
# Enum for specifying a sub-project
########################################


class ProjectContext(Enum):
    """An Enum to track the possible docker targets and images."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    PULUMI = "pulumi"
    ALL = "all"
