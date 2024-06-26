"""Task for setting up a new project.

This module exists to have a single task and code location where all
the logic for making a new project is executed from.
"""

from typing import override

from build_support.ci_cd_tasks.env_setup_tasks import Clean
from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_new_project_settings,
)
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.project_structure import get_license_file
from build_support.new_project_setup.new_project_data_models import ProjectSettings
from build_support.new_project_setup.setup_license import (
    write_new_license_from_template,
)
from build_support.new_project_setup.update_folder_names import (
    update_folders_in_project,
)
from build_support.new_project_setup.update_pyproject_toml import update_pyproject_toml
from build_support.new_project_setup.update_readme_md import update_readme


class MakeProjectFromTemplate(TaskNode):
    """Updates project based on the project settings yaml."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the list of tasks to run before setting up a new project.

        Returns:
            list[TaskNode]: A list of tasks required to build a new project. [Clean]
        """
        return [Clean(basic_task_info=self.get_basic_task_info())]

    @override
    def run(self) -> None:
        """Modifies the appropriate files to start a new project.

        Returns:
            None
        """
        original_project_name = get_project_name(project_root=self.docker_project_root)
        new_project_settings = ProjectSettings.from_yaml(
            yaml_str=get_new_project_settings(
                project_root=self.docker_project_root,
            ).read_text(),
        )
        update_readme(
            project_root=self.docker_project_root,
            original_project_name=original_project_name,
            new_project_settings=new_project_settings,
        )
        write_new_license_from_template(
            license_file_path=get_license_file(project_root=self.docker_project_root),
            template_key=new_project_settings.license,
            organization=new_project_settings.organization,
        )
        update_folders_in_project(
            project_root=self.docker_project_root,
            original_project_name=original_project_name,
            new_project_settings=new_project_settings,
        )
        update_pyproject_toml(
            project_root=self.docker_project_root,
            new_project_settings=new_project_settings,
        )
