"""Module exists to conceptually organize all changes to the pyproject.toml file."""

from pathlib import Path
from typing import cast

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
    project = cast(TOMLDocument, pyproject_data["project"])
    project["name"] = new_project_settings.name
    project["version"] = "0.0.0"
    project["license"] = new_project_settings.license
    project["authors"] = [new_project_settings.organization.as_pyproject_author()]
    tool = cast(TOMLDocument, pyproject_data["tool"])
    hatch = cast(TOMLDocument, tool["hatch"])
    hatch_build = cast(TOMLDocument, hatch["build"])
    targets = cast(TOMLDocument, hatch_build["targets"])
    wheel = cast(TOMLDocument, targets["wheel"])
    wheel["packages"] = [f"pypi_package/src/{new_project_settings.name}"]
    path_to_pyproject_toml.write_text(dumps(pyproject_data))
