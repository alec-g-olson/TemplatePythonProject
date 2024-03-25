"""Module exists to keep the logic for updating and changing the README.md isolated."""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_readme
from build_support.new_project_setup.new_project_data_models import ProjectSettings


def update_readme(
    project_root: Path,
    original_project_name: str,
    new_project_settings: ProjectSettings,
) -> None:
    """Updates the README.md based on the new project settings.

    Args:
        project_root (Path): Path to this project's root.
        original_project_name (str): The old name of the project.
        new_project_settings (ProjectSettings): The information needed to create a new
            project.

    Returns:
        None
    """
    readme_path = get_readme(project_root=project_root)
    new_project_name = new_project_settings.name
    old_readme_contents = readme_path.read_text()
    new_readme_contents = old_readme_contents.replace(
        original_project_name, new_project_name
    )
    readme_path.write_text(new_readme_contents)
