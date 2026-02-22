import shutil
from copy import deepcopy
from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import get_pyproject_toml_data
from build_support.ci_cd_vars.project_structure import get_pyproject_toml
from build_support.new_project_setup.new_project_data_models import (
    Organization,
    ProjectSettings,
)
from build_support.new_project_setup.update_pyproject_toml import update_pyproject_toml


def test_update_pyproject_toml(tmp_path: Path, real_project_root_dir: Path) -> None:
    tmp_project_path = tmp_path.joinpath("template_python_project")
    tmp_project_path.mkdir(parents=True, exist_ok=True)
    original_pyproject_toml = get_pyproject_toml(project_root=real_project_root_dir)
    test_pyproject_toml = get_pyproject_toml(project_root=tmp_project_path)
    shutil.copy(original_pyproject_toml, test_pyproject_toml)

    original_data = get_pyproject_toml_data(project_root=tmp_project_path)
    new_project_settings = ProjectSettings(
        name="open_source_project",
        license="mit",
        organization=Organization(
            name="A Very Nice Person",
            contact_email="tastefully.zanny.email@selfhosted.com",
        ),
    )
    expected_data = deepcopy(original_data)
    update_pyproject_toml(
        project_root=tmp_project_path, new_project_settings=new_project_settings
    )

    expected_project = expected_data["project"]  # type: ignore[index]
    expected_project["name"] = new_project_settings.name  # type: ignore[index]
    expected_project["version"] = "0.0.0"  # type: ignore[index]
    expected_project["license"] = new_project_settings.license  # type: ignore[index]
    expected_project["authors"] = [  # type: ignore[index]
        new_project_settings.organization.formatted_name_and_email()
    ]
    expected_hatch = expected_data["tool"]["hatch"]  # type: ignore[index]
    expected_hatch["build"]["targets"]["wheel"]["packages"] = [  # type: ignore[index]
        f"pypi_package/src/{new_project_settings.name}"
    ]

    observed_new_pyproject_toml = get_pyproject_toml_data(project_root=tmp_project_path)
    assert observed_new_pyproject_toml == expected_data
