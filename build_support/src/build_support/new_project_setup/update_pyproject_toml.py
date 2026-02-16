"""Module exists to conceptually organize all changes to the pyproject.toml file."""

from pathlib import Path

from tomlkit import TOMLDocument, dumps

from build_support.ci_cd_vars.project_setting_vars import get_pyproject_toml_data
from build_support.ci_cd_vars.project_structure import get_pyproject_toml
from build_support.new_project_setup.new_project_data_models import ProjectSettings


def update_pyproject_toml(
    project_root: Path, new_project_settings: ProjectSettings
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
    pyproject_data: TOMLDocument = get_pyproject_toml_data(project_root=project_root)
    poetry = pyproject_data["tool"]["poetry"]  # type: ignore[index]
    poetry["name"] = new_project_settings.name  # type: ignore[index]
    poetry["version"] = "0.0.0"  # type: ignore[index]
    poetry["license"] = new_project_settings.license  # type: ignore[index]
    poetry["authors"] = [  # type: ignore[index]
        new_project_settings.organization.formatted_name_and_email()
    ]
    poetry["packages"][0]["include"] = (  # type: ignore[index]
        new_project_settings.name
    )
    path_to_pyproject_toml.write_text(dumps(pyproject_data))
