import shutil
import tomllib
from pathlib import Path

from build_tasks.common_build_tasks import MakeProjectFromTemplate, ProjectSettings


def _ensure_project_folder_matches_settings(
    project_folder: Path, settings: ProjectSettings, version_reset: bool
):
    pyproject_toml_path = project_folder.joinpath("pyproject.toml")
    pyproject_toml_data = tomllib.loads(pyproject_toml_path.read_text())
    print(pyproject_toml_data)
    assert pyproject_toml_data["tool"]["poetry"]["name"] == settings.name
    assert (
        pyproject_toml_data["tool"]["poetry"]["version"] == "0.0.0"
    ) == version_reset


def test_make_new_project(tmp_path: Path, project_root_dir: Path):
    print(tmp_path)
    tmp_project_path = tmp_path.joinpath("template_python_project")
    shutil.copytree(project_root_dir, tmp_project_path)
    project_settings_path = tmp_project_path.joinpath(
        "build_support", "project_settings.json"
    )
    original_project_settings = ProjectSettings.from_json(
        project_settings_path.read_text()
    )
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        settings=original_project_settings,
        version_reset=False,
    )
    modified_project_settings = ProjectSettings(name="modified_project")
    project_settings_path.write_text(modified_project_settings.to_json())
    make_project_task = MakeProjectFromTemplate()
    make_project_task.run(
        non_docker_project_root=tmp_project_path,
        docker_project_root=tmp_project_path,
        local_username="Not used",
    )
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        settings=modified_project_settings,
        version_reset=True,
    )