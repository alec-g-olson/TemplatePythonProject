"""Module exists to conceptually organize all changes to the pyproject.toml file."""

from pathlib import Path
from typing import Any

from new_project_setup.new_project_dataclass import ProjectSettings
from tomlkit import dumps, parse


def update_pyproject_toml(
    path_to_pyproject_toml: Path, new_project_settings: ProjectSettings
) -> None:
    """Updates the pyproject toml based on the new project settings."""
    # Forced type because mypy can't recognize TOMLDocument properties
    pyproject_data: dict[Any, Any] = parse(path_to_pyproject_toml.read_text())
    pyproject_data["tool"]["poetry"]["name"] = new_project_settings.name
    pyproject_data["tool"]["poetry"]["version"] = "0.0.0"
    pyproject_data["tool"]["poetry"]["license"] = new_project_settings.license
    pyproject_data["tool"]["poetry"]["authors"] = [new_project_settings.organization]
    path_to_pyproject_toml.write_text(dumps(pyproject_data))
