import shutil
from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
)
from build_support.ci_cd_vars.project_structure import get_readme
from build_support.new_project_setup.new_project_data_models import (
    Organization,
    ProjectSettings,
)
from build_support.new_project_setup.update_readme_md import update_readme


def test_update_readme(tmp_path: Path, real_project_root_dir: Path) -> None:
    tmp_project_path = tmp_path.joinpath("template_python_project")
    tmp_project_path.mkdir(parents=True, exist_ok=True)
    original_readme = get_readme(project_root=real_project_root_dir)
    test_readme = get_readme(project_root=tmp_project_path)
    shutil.copy(original_readme, test_readme)

    original_readme_contents = test_readme.read_text()
    new_project_settings = ProjectSettings(
        name="open_source_project",
        license="mit",
        organization=Organization(
            name="A Very Nice Person",
            contact_email="tastefully.zanny.email@selfhosted.com",
        ),
    )
    original_project_name = get_project_name(project_root=real_project_root_dir)
    update_readme(
        project_root=tmp_project_path,
        original_project_name=original_project_name,
        new_project_settings=new_project_settings,
    )

    expected_readme_contents = original_readme_contents.replace(
        original_project_name, new_project_settings.name
    )

    observed_readme_contents = test_readme.read_text()
    assert expected_readme_contents == observed_readme_contents
