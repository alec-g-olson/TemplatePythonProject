"""Collection of all file and folder path functions and variables."""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_build_dir, maybe_build_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
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
    process_and_style_subproject = get_python_subproject(
        subproject_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
        project_root=project_root,
    )
    return process_and_style_subproject.get_subproject_root().joinpath(
        "sphinx_conf",
    )


########################################
# Extra files and folders contained in build_support
########################################


def get_new_project_settings(project_root: Path) -> Path:
    """Get a path to the new_project_settings.yaml file in this project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Path: Path to the new_project_settings.yaml file in this project.
    """
    build_support_subproject = get_python_subproject(
        subproject_context=SubprojectContext.BUILD_SUPPORT, project_root=project_root
    )
    return build_support_subproject.get_subproject_root().joinpath(
        "new_project_settings.yaml",
    )


########################################
# Extra files and folders contained in pulumi
########################################


########################################
# Extra files and folder contained in pypi_package
########################################


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


def get_all_python_folders(project_root: Path) -> list[Path]:
    """Gets all the python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the python folders in the project.
    """
    subprojects = get_all_python_subprojects_dict(project_root=project_root)
    return [
        python_folder
        for subproject in subprojects.values()
        for python_folder in subproject.get_subproject_src_and_test_dir()
        if python_folder.exists()
    ] + [get_sphinx_conf_dir(project_root=project_root)]


def get_all_non_pulumi_python_folders(project_root: Path) -> list[Path]:
    """Gets all the non-pulumi python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the non-pulumi python folders in the project.
    """
    pulumi_subproject = get_python_subproject(
        subproject=SubprojectContext.PULUMI, project_root=project_root
    )
    pulumi_folders = pulumi_subproject.get_subproject_src_and_test_dir()
    return [
        folder
        for folder in get_all_python_folders(project_root=project_root)
        if folder not in pulumi_folders
    ]


def get_all_src_folders(project_root: Path) -> list[Path]:
    """Gets all the python src folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the python src folders in the project.
    """
    subprojects = get_all_python_subprojects_dict(project_root=project_root)
    src_dirs = [
        subproject.get_subproject_src_dir() for subproject in subprojects.values()
    ]
    return [src_dir for src_dir in src_dirs if src_dir.exists()]


def get_all_test_folders(project_root: Path) -> list[Path]:
    """Gets all the python test folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the python test folders in the project.
    """
    subprojects = get_all_python_subprojects_dict(project_root=project_root)
    test_dirs = [
        subproject.get_subproject_test_dir() for subproject in subprojects.values()
    ]
    return [test_dir for test_dir in test_dirs if test_dir.exists()]


def get_all_non_test_folders(project_root: Path) -> list[Path]:
    """Gets all the non-test python folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the non-test pytho folders in the project.
    """
    all_folders = get_all_python_folders(project_root=project_root)
    test_folders = get_all_test_folders(project_root=project_root)
    return [folder for folder in all_folders if folder not in test_folders]
