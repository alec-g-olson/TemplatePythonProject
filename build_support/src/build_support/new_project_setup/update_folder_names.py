"""Module for changing file and folder names when setting up a new project."""
from pathlib import Path

from build_support.ci_cd_vars.file_and_dir_path_vars import get_pypi_src_dir
from build_support.new_project_setup.new_project_data_models import ProjectSettings


def update_folders_in_project(
    project_root: Path,
    original_project_name: str,
    new_project_settings: ProjectSettings,
) -> None:
    """Updates the pyproject toml based on the new project settings."""
    pypi_src_dir = get_pypi_src_dir(project_root=project_root)
    original_package_dir = pypi_src_dir.joinpath(original_project_name)
    new_package_dir = pypi_src_dir.joinpath(new_project_settings.name)
    original_package_dir.rename(new_package_dir)
