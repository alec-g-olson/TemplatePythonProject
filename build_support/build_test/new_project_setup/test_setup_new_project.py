import shutil
import tomllib
from pathlib import Path

from new_project_setup.new_project_dataclass import ProjectSettings
from new_project_setup.setup_license import (
    ALL_RIGHTS_RESERVED_KEY,
    get_new_license_content,
)
from new_project_setup.setup_new_project import MakeProjectFromTemplate


def _check_pyproject_toml(
    pyproject_toml_path: Path, settings: ProjectSettings, version_reset: bool
):
    pyproject_toml_data = tomllib.loads(pyproject_toml_path.read_text())
    assert pyproject_toml_data["tool"]["poetry"]["name"] == settings.name
    assert (
        pyproject_toml_data["tool"]["poetry"]["version"] == "0.0.0"
    ) == version_reset
    assert pyproject_toml_data["tool"]["poetry"]["license"] == settings.license
    assert pyproject_toml_data["tool"]["poetry"]["authors"] == [settings.organization]


def _check_license_file(license_path: Path, settings: ProjectSettings):
    expected_license_content = get_new_license_content(
        template_key=settings.license, organization=settings.organization
    )
    observed_license_content = license_path.read_text()
    assert observed_license_content == expected_license_content


def _ensure_project_folder_matches_settings(
    project_folder: Path, settings: ProjectSettings, version_reset: bool
):
    _check_pyproject_toml(
        pyproject_toml_path=project_folder.joinpath("pyproject.toml"),
        settings=settings,
        version_reset=version_reset,
    )
    _check_license_file(
        license_path=project_folder.joinpath("LICENSE"), settings=settings
    )


def test_make_new_project(tmp_path: Path, project_root_dir: Path):
    tmp_project_path = tmp_path.joinpath("template_python_project")
    shutil.copytree(project_root_dir, tmp_project_path)
    project_settings_path = tmp_project_path.joinpath(
        "build_support", "project_settings.yaml"
    )
    original_project_settings = ProjectSettings.from_yaml(
        project_settings_path.read_text()
    )
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        settings=original_project_settings,
        version_reset=False,
    )
    modified_project_settings = ProjectSettings(
        name="open_source_project",
        license="mit",
        organization="A Very Nice Person <tastefully.zanny.email@selfhosted.com>",
    )
    project_settings_path.write_text(modified_project_settings.to_yaml())
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
    modified_project_settings = ProjectSettings(
        name="closed_source_project",
        license=ALL_RIGHTS_RESERVED_KEY,
        organization="Soulless Corp. 3000 <our.lawyers.are.mean@soulless.io>",
    )
    project_settings_path.write_text(modified_project_settings.to_yaml())
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
