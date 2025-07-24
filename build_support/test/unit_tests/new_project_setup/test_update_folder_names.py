import shutil
from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.new_project_setup.new_project_data_models import (
    Organization,
    ProjectSettings,
)
from build_support.new_project_setup.update_folder_names import (
    update_folders_in_project,
)


def test_update_folders_in_project(tmp_path: Path, real_project_root_dir: Path) -> None:
    tmp_project_path = tmp_path.joinpath("template_python_project")
    shutil.copytree(real_project_root_dir, tmp_project_path)

    expected_relative_path_strs = set()

    for p in tmp_project_path.rglob("*"):
        original_relative_path = str(p.relative_to(tmp_project_path))
        expected_relative_path_strs.add(original_relative_path)

    new_project_settings = ProjectSettings(
        name="open_source_project",
        license="mit",
        organization=Organization(
            name="A Very Nice Person",
            contact_email="tastefully.zanny.email@selfhosted.com",
        ),
    )
    original_project_name = get_project_name(project_root=real_project_root_dir)
    update_folders_in_project(
        project_root=tmp_project_path,
        original_project_name=original_project_name,
        new_project_settings=new_project_settings,
    )

    pypi_src_dir = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=tmp_project_path
    ).get_src_dir()
    original_package_dir = pypi_src_dir.joinpath(original_project_name)
    new_package_dir = pypi_src_dir.joinpath(new_project_settings.name)
    original_relative_path = str(original_package_dir.relative_to(tmp_project_path))
    expected_relative_path = str(new_package_dir.relative_to(tmp_project_path))

    expected_relative_path_strs.remove(original_relative_path)
    expected_relative_path_strs.add(expected_relative_path)

    observed_paths = list(tmp_project_path.rglob("*"))

    assert len(observed_paths) == len(expected_relative_path_strs)

    assert all(
        tmp_project_path.joinpath(relative_path).exists()
        for relative_path in observed_paths
    )
