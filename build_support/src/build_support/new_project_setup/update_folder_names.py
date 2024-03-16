"""Module for changing file and folder names when setting up a new project."""

from pathlib import Path

from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.new_project_setup.new_project_data_models import ProjectSettings


def update_folders_in_project(
    project_root: Path,
    original_project_name: str,
    new_project_settings: ProjectSettings,
) -> None:
    """Updates the names of some folders based on the new project settings.

    Args:
        project_root (Path): Path to this project's root.
        original_project_name (str): The project name of the template being used to
            create a new project.
        new_project_settings (ProjectSettings): The information needed to create a new
            project.

    Returns:
        None
    """
    pypi_src_dir = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=project_root
    ).get_subproject_src_dir()
    original_package_dir = pypi_src_dir.joinpath(original_project_name)
    new_package_dir = pypi_src_dir.joinpath(new_project_settings.name)
    original_package_dir.rename(new_package_dir)
