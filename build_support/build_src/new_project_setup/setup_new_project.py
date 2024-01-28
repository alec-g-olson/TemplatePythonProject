"""Task for setting up a new project.

This module exists to have a single task and code location where all
the logic for making a new project is executed from.
"""
from pathlib import Path

from build_tasks.common_build_tasks import Clean
from common_vars import get_license_file, get_new_project_settings, get_pyproject_toml
from dag_engine import TaskNode
from new_project_setup.new_project_dataclass import ProjectSettings
from new_project_setup.setup_license import write_new_license_from_template
from new_project_setup.update_pyproject import update_pyproject_toml


class MakeProjectFromTemplate(TaskNode):
    """Updates project based on the project settings yaml."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return [Clean()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Modifies the appropriate files to start a new project."""
        new_project_settings = ProjectSettings.from_yaml(
            get_new_project_settings(project_root=docker_project_root).read_text()
        )
        update_pyproject_toml(
            path_to_pyproject_toml=get_pyproject_toml(project_root=docker_project_root),
            new_project_settings=new_project_settings,
        )
        write_new_license_from_template(
            license_file_path=get_license_file(project_root=docker_project_root),
            template_key=new_project_settings.license,
            organization=new_project_settings.organization,
        )
