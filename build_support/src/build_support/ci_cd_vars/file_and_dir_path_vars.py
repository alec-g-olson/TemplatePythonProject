"""Collection of all file and folder path functions and variables."""

from enum import Enum
from pathlib import Path

from build_support.dag_engine import concatenate_args


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
    """Get a path to the poetry.lock file in a project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the poetry.lock file in this project.
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


def get_build_support_dir(project_root: Path) -> Path:
    """Gets the build_support directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build_support directory for this project.
    """
    return project_root.joinpath("build_support")


def get_dockerfile(project_root: Path) -> Path:
    """Gets the Dockerfile for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the Dockerfile for this project.
    """
    return project_root.joinpath("Dockerfile")


def get_pypi_dir(project_root: Path) -> Path:
    """Gets the PyPi directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi directory for this project.
    """
    return project_root.joinpath("pypi_package")


def get_pulumi_dir(project_root: Path) -> Path:
    """Gets the pulumi directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the pulumi directory for this project.
    """
    return project_root.joinpath("pulumi")


def get_process_and_style_enforcement_dir(project_root: Path) -> Path:
    """Gets the documentation enforcement directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the documentation enforcement directory for this project.
    """
    return project_root.joinpath("process_and_style_enforcement")


########################################
# Subproject folder structure
########################################


def get_subproject_src_dir(subproject_root: Path) -> Path:
    """Gets the src folder in a subproject.

    Args:
        subproject_root (Path): Root directory of the subproject.

    Returns:
        Path: Path to the src folder in the subproject.
    """
    return subproject_root.joinpath("src")


def get_subproject_test_dir(subproject_root: Path) -> Path:
    """Gets the test folder in a subproject.

    Args:
        subproject_root (Path): Root directory of the subproject.

    Returns:
        Path: Path to the test folder in the subproject.
    """
    return subproject_root.joinpath("test")


def get_subproject_docs_dir(subproject_root: Path) -> Path:
    """Gets the documents folder in a subproject.

    Args:
        subproject_root (Path): Root directory of the subproject.

    Returns:
        Path: Path to the docs folder in the subproject.
    """
    return subproject_root.joinpath("docs")


def get_subproject_docs_source_dir(subproject_root: Path) -> Path:
    """Gets the documentation source folder in a subproject.

    Args:
        subproject_root (Path): Root directory of the subproject.

    Returns:
        Path: Path to the documentation source folder in the subproject.
    """
    return get_subproject_docs_dir(subproject_root=subproject_root).joinpath("source")


def get_subproject_docs_build_dir(subproject_root: Path) -> Path:
    """Gets the documentation build folder in a subproject.

    Args:
        subproject_root (Path): Root directory of the subproject.

    Returns:
        Path: Path to the documentation build folder in the subproject.
    """
    return maybe_build_dir(
        dir_to_build=get_subproject_docs_dir(subproject_root=subproject_root).joinpath(
            "build",
        ),
    )


########################################
# Files and folders contained in process_and_style_enforcement
########################################


def get_sphinx_conf_dir(project_root: Path) -> Path:
    """Gets the sphinx config file for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the sphinx config directory in this project.
    """
    return get_process_and_style_enforcement_dir(project_root=project_root).joinpath(
        "sphinx_conf",
    )


def get_documentation_tests_dir(project_root: Path) -> Path:
    """Gets the documentation tests directory for this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the documentation tests directory for this project.
    """
    return get_process_and_style_enforcement_dir(project_root=project_root).joinpath(
        "test"
    )


########################################
# Files and folders contained in build_support
########################################


def get_new_project_settings(project_root: Path) -> Path:
    """Get a path to the new_project_settings.yaml file in this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the new_project_settings.yaml file in this project.
    """
    return get_build_support_dir(project_root=project_root).joinpath(
        "new_project_settings.yaml",
    )


def get_build_support_src_dir(project_root: Path) -> Path:
    """Gets the build_support src dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build_support src dir in this project.
    """
    return get_subproject_src_dir(
        subproject_root=get_build_support_dir(project_root=project_root),
    )


def get_build_support_test_dir(project_root: Path) -> Path:
    """Gets the build_support test dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build_support test dir in this project.
    """
    return get_subproject_test_dir(
        subproject_root=get_build_support_dir(project_root=project_root),
    )


def get_build_support_docs_src_dir(project_root: Path) -> Path:
    """Gets the build_support documents source dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build_support documents source dir in this project.
    """
    return get_subproject_docs_source_dir(
        subproject_root=get_build_support_dir(project_root=project_root),
    )


def get_build_support_docs_build_dir(project_root: Path) -> Path:
    """Gets the build_support documents build dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the build_support documents build dir in this project.
    """
    return get_subproject_docs_build_dir(
        subproject_root=get_build_support_dir(project_root=project_root),
    )


def get_build_support_src_and_test(project_root: Path) -> list[str]:
    """Gets the build_support src and test dirs for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to the build_support src and test dirs for the project.
    """
    return concatenate_args(
        args=[
            get_build_support_src_dir(project_root=project_root),
            get_build_support_test_dir(project_root=project_root),
        ],
    )


########################################
# Files and folders contained in pulumi
########################################


########################################
# Files and folder contained in pypi_package
########################################


def get_pypi_src_dir(project_root: Path) -> Path:
    """Gets the PyPi src dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi src dir in this project.
    """
    return get_subproject_src_dir(
        subproject_root=get_pypi_dir(project_root=project_root),
    )


def get_pypi_test_dir(project_root: Path) -> Path:
    """Gets the PyPi test dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi test dir in this project.
    """
    return get_subproject_test_dir(
        subproject_root=get_pypi_dir(project_root=project_root),
    )


def get_pypi_docs_src_dir(project_root: Path) -> Path:
    """Gets the PyPi documents source dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi documents source dir in this project.
    """
    return get_subproject_docs_source_dir(
        subproject_root=get_pypi_dir(project_root=project_root),
    )


def get_pypi_docs_build_dir(project_root: Path) -> Path:
    """Gets the PyPi documents build dir for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi documents build dir in this project.
    """
    return get_subproject_docs_build_dir(
        subproject_root=get_pypi_dir(project_root=project_root),
    )


def get_pypi_src_and_test(project_root: Path) -> list[str]:
    """Gets the PyPi src and test dirs for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to the PyPi src and test dirs for the project.
    """
    return concatenate_args(
        args=[
            get_pypi_src_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
        ],
    )


########################################
# Files and folders used during build process
########################################


def get_dist_dir(project_root: Path) -> Path:
    """Gets the directory where the PyPi distribution will be built.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi dist directory for this project.
    """
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("dist"),
    )


def get_build_reports_dir(project_root: Path) -> Path:
    """Gets the directory that will contain the project's reports.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the directory that will contain the project's reports.
    """
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("reports"),
    )


def get_license_templates_dir(project_root: Path) -> Path:
    """Gets the dir that will contain license templates used in building a new project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the directory that will contain license templates used in
            building a new project.
    """
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath(
            "license_templates",
        ),
    )


def get_git_info_yaml(project_root: Path) -> Path:
    """Gets the location of the git_info.yaml for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the git_info.yaml for the project.
    """
    return get_build_dir(project_root=project_root).joinpath("git_info.yaml")


########################################
# Files and folder collections that span domains
########################################


def get_all_non_pulumi_python_folders(project_root: Path) -> list[str]:
    """Gets all the non-pulumi python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to all the non-pulumi python folders in the project.
    """
    return concatenate_args(
        args=[
            get_build_support_src_and_test(project_root=project_root),
            get_pypi_src_and_test(project_root=project_root),
            get_documentation_tests_dir(project_root=project_root),
        ],
    )


def get_all_python_folders(project_root: Path) -> list[str]:
    """Gets all the python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to all the python folders in the project.
    """
    return concatenate_args(
        args=[
            get_all_non_pulumi_python_folders(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
            get_sphinx_conf_dir(project_root=project_root),
        ],
    )


def get_all_src_folders(project_root: Path) -> list[str]:
    """Gets all the python src folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to all the python src folders in the project.
    """
    return concatenate_args(
        args=[
            get_build_support_src_dir(project_root=project_root),
            get_pypi_src_dir(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
        ],
    )


def get_all_test_folders(project_root: Path) -> list[str]:
    """Gets all the python test folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to all the python test folders in the project.
    """
    return concatenate_args(
        args=[
            get_build_support_test_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
            get_documentation_tests_dir(project_root=project_root),
        ],
    )


def get_all_non_test_folders(project_root: Path) -> list[str]:
    """Gets all the non-test python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: Path to all the non-test pytho folders in the project.
    """
    return [
        path
        for path in get_all_python_folders(project_root=project_root)
        if path not in get_all_test_folders(project_root=project_root)
    ]


########################################
# Enum for specifying a sub-project
########################################


class SubprojectContext(Enum):
    """An Enum to track the possible docker targets and images."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    PULUMI = "pulumi"
    DOCUMENTATION_ENFORCEMENT = "process_and_style_enforcement"
    ALL = "all"
