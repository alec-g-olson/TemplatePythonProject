"""Contains functions for paths to files and directories within the build directory.

The build directory contains all artifacts, reports, and temporary files generated
during the build process.
"""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_build_dir, maybe_build_dir

########################################
# Build directories
########################################


def get_dist_dir(project_root: Path) -> Path:
    """Gets the directory where the PyPi distribution will be built.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the PyPi dist directory for this project.
    """
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("dist")
    )


def get_build_docs_dir(project_root: Path) -> Path:
    """Gets the dir that will be used for building the documentation of this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the directory that this project's documentation will be built in.
    """
    return maybe_build_dir(
        dir_to_build=get_build_dir(project_root=project_root).joinpath("docs")
    )


def get_build_docs_source_dir(project_root: Path) -> Path:
    """Gets the dir that will hold the source files for this project's documentation.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the directory for this project's documentation sphinx sources.
    """
    return maybe_build_dir(
        dir_to_build=get_build_docs_dir(project_root=project_root).joinpath("source")
    )


def get_build_docs_build_dir(project_root: Path) -> Path:
    """Gets the dir that will hold this project's sphinx documentation.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the directory for this project's final sphinx documentation.
    """
    return maybe_build_dir(
        dir_to_build=get_build_docs_dir(project_root=project_root).joinpath("build")
    )


########################################
# Build files
########################################


def get_local_info_yaml(project_root: Path) -> Path:
    """Gets the location of the local_info.yaml for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the local_info.yaml for the project.
    """
    return get_build_dir(project_root=project_root).joinpath("local_info.yaml")


def get_git_info_yaml(project_root: Path) -> Path:
    """Gets the location of the git_info.yaml for the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the git_info.yaml for the project.
    """
    return get_build_dir(project_root=project_root).joinpath("git_info.yaml")


def get_build_runtime_report_path(project_root: Path) -> Path:
    """Gets the path to the build runtime report file.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the file that will have the build runtime report.
    """
    return get_build_dir(project_root=project_root).joinpath("build_runtime.yaml")
