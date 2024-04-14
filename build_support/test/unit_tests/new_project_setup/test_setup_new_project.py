import shutil
import tomllib
from pathlib import Path

from build_support.ci_cd_tasks.env_setup_tasks import Clean
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.new_project_setup.license_templates import ALL_RIGHTS_RESERVED_KEY
from build_support.new_project_setup.new_project_data_models import (
    Organization,
    ProjectSettings,
)
from build_support.new_project_setup.setup_license import get_new_license_content
from build_support.new_project_setup.setup_new_project import MakeProjectFromTemplate


def _check_pyproject_toml(
    pyproject_toml_path: Path,
    settings: ProjectSettings,
    version_reset: bool,
) -> None:
    pyproject_toml_data = tomllib.loads(pyproject_toml_path.read_text())
    assert pyproject_toml_data["tool"]["poetry"]["name"] == settings.name
    assert (
        pyproject_toml_data["tool"]["poetry"]["version"] == "0.0.0"
    ) == version_reset
    assert pyproject_toml_data["tool"]["poetry"]["license"] == settings.license
    assert pyproject_toml_data["tool"]["poetry"]["authors"] == [
        settings.organization.formatted_name_and_email(),
    ]
    assert len(pyproject_toml_data["tool"]["poetry"]["packages"]) == 1
    assert (
        pyproject_toml_data["tool"]["poetry"]["packages"][0]["include"] == settings.name
    )


def _check_readme(
    readme_path: Path, new_project_name: str, old_project_name: str | None
) -> None:
    readme_contents = readme_path.read_text()
    if old_project_name:
        assert old_project_name not in readme_contents
    assert new_project_name in readme_contents


def _check_license_file(license_path: Path, settings: ProjectSettings) -> None:
    expected_license_content = get_new_license_content(
        template_key=settings.license,
        organization=settings.organization,
    )
    observed_license_content = license_path.read_text()
    assert observed_license_content == expected_license_content


def _check_folder_names(project_folder: Path, settings: ProjectSettings) -> None:
    pypi_subproject = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=project_folder
    )
    assert pypi_subproject.get_src_dir().joinpath(settings.name).exists()


def _ensure_project_folder_matches_settings(
    project_folder: Path,
    new_settings: ProjectSettings,
    version_reset: bool,
    old_settings: ProjectSettings | None = None,
) -> None:
    _check_pyproject_toml(
        pyproject_toml_path=project_folder.joinpath("pyproject.toml"),
        settings=new_settings,
        version_reset=version_reset,
    )
    _check_license_file(
        license_path=project_folder.joinpath("LICENSE"),
        settings=new_settings,
    )
    _check_folder_names(project_folder=project_folder, settings=new_settings)
    _check_readme(
        readme_path=project_folder.joinpath("README.md"),
        new_project_name=new_settings.name,
        old_project_name=old_settings.name if old_settings else None,
    )


def test_make_new_project(tmp_path: Path, real_project_root_dir: Path) -> None:
    tmp_project_path = tmp_path.joinpath("template_python_project")
    shutil.copytree(real_project_root_dir, tmp_project_path)
    project_settings_path = tmp_project_path.joinpath(
        "build_support",
        "new_project_settings.yaml",
    )
    original_project_settings = ProjectSettings.from_yaml(
        project_settings_path.read_text(),
    )
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        new_settings=original_project_settings,
        version_reset=False,
    )
    modified_project_settings_1 = ProjectSettings(
        name="open_source_project",
        license="mit",
        organization=Organization(
            name="A Very Nice Person",
            contact_email="tastefully.zanny.email@selfhosted.com",
        ),
    )
    project_settings_path.write_text(modified_project_settings_1.to_yaml())
    make_project_task = MakeProjectFromTemplate(
        basic_task_info=BasicTaskInfo(
            non_docker_project_root=tmp_project_path,
            docker_project_root=tmp_project_path,
            local_uid=10,
            local_gid=2,
            local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
        )
    )
    make_project_task.run()
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        old_settings=original_project_settings,
        new_settings=modified_project_settings_1,
        version_reset=True,
    )
    modified_project_settings_2 = ProjectSettings(
        name="closed_source_project",
        license=ALL_RIGHTS_RESERVED_KEY,
        organization=Organization(
            name="Soulless Corp. 3000",
            contact_email="our.lawyers.are.mean@soulless.io",
        ),
    )
    project_settings_path.write_text(modified_project_settings_2.to_yaml())
    make_project_task = MakeProjectFromTemplate(
        basic_task_info=BasicTaskInfo(
            non_docker_project_root=tmp_project_path,
            docker_project_root=tmp_project_path,
            local_uid=10,
            local_gid=2,
            local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
        )
    )
    make_project_task.run()
    _ensure_project_folder_matches_settings(
        project_folder=tmp_project_path,
        old_settings=modified_project_settings_1,
        new_settings=modified_project_settings_2,
        version_reset=True,
    )


def test_setup_new_project_requires(tmp_path: Path) -> None:
    tmp_project_path = tmp_path.joinpath("template_python_project")
    assert MakeProjectFromTemplate(
        basic_task_info=BasicTaskInfo(
            non_docker_project_root=tmp_project_path,
            docker_project_root=tmp_project_path,
            local_uid=10,
            local_gid=2,
            local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
        )
    ).required_tasks() == [
        Clean(
            basic_task_info=BasicTaskInfo(
                non_docker_project_root=tmp_project_path,
                docker_project_root=tmp_project_path,
                local_uid=10,
                local_gid=2,
                local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
            )
        )
    ]
