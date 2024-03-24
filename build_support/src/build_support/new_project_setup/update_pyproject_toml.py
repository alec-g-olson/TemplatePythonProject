"""Module exists to conceptually organize all changes to the pyproject.toml file."""

from pathlib import Path
from typing import Any

from tomlkit import dumps, parse

from build_support.ci_cd_vars.project_structure import get_pyproject_toml
from build_support.new_project_setup.new_project_data_models import ProjectSettings


def update_pyproject_toml(
    project_root: Path,
    new_project_settings: ProjectSettings,
) -> None:
    """Updates the pyproject toml based on the new project settings.

    Args:
        project_root (Path): Path to this project's root.
        new_project_settings (ProjectSettings): The information needed to create a new
            project.

    Returns:
        None
    """
    path_to_pyproject_toml = get_pyproject_toml(project_root=project_root)
    # Forced type because mypy can't recognize TOMLDocument properties
    pyproject_data: dict[Any, Any] = parse(path_to_pyproject_toml.read_text())
    pyproject_data["tool"]["poetry"]["name"] = new_project_settings.name
    pyproject_data["tool"]["poetry"]["version"] = "0.0.0"
    pyproject_data["tool"]["poetry"]["license"] = new_project_settings.license
    pyproject_data["tool"]["poetry"]["authors"] = [
        new_project_settings.organization.formatted_name_and_email(),
    ]
    pyproject_data["tool"]["poetry"]["packages"][0]["include"] = (
        new_project_settings.name
    )
    path_to_pyproject_toml.write_text(dumps(pyproject_data))
