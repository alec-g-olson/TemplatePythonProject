"""Collection of functions that aggregate paths across multiple subprojects.

These functions combine top-level project features and operate on collections of
paths from different parts of the project structure.
"""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_sphinx_conf_dir
from build_support.ci_cd_vars.subproject_structure import (
    get_all_python_subprojects_dict,
    get_all_python_subprojects_with_src,
    get_all_python_subprojects_with_test,
)

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
    python_folders = [
        python_folder
        for subproject in subprojects.values()
        for python_folder in (subproject.get_src_dir(), subproject.get_test_dir())
        if python_folder.exists()
    ] + [get_sphinx_conf_dir(project_root=project_root)]
    return sorted(python_folders)


def get_all_src_folders(project_root: Path) -> list[Path]:
    """Gets all the python src folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the python src folders in the project.
    """
    src_dirs = sorted(
        subproject.get_src_dir()
        for subproject in get_all_python_subprojects_with_src(project_root=project_root)
    )
    return [src_dir for src_dir in src_dirs if src_dir.exists()]


def get_all_test_folders(project_root: Path) -> list[Path]:
    """Gets all the python test folders in the project.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all the python test folders in the project.
    """
    test_dirs = sorted(
        subproject.get_test_dir()
        for subproject in get_all_python_subprojects_with_test(
            project_root=project_root
        )
    )
    return [test_dir for test_dir in test_dirs if test_dir.exists()]


def get_test_utils_dirs(project_root: Path) -> list[Path]:
    """Gets all test_utils directories in the project.

    The test_utils folder contains utility Python source files that are used by
    test files but are not test files themselves. These directories need to be in
    MYPYPATH so mypy can resolve imports from test files.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[Path]: Path to all test_utils directories in the project that exist.
    """
    test_utils_dirs = sorted(
        subproject.get_test_utils_dir()
        for subproject in get_all_python_subprojects_with_test(
            project_root=project_root
        )
    )
    return [
        test_utils_dir for test_utils_dir in test_utils_dirs if test_utils_dir.exists()
    ]


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
