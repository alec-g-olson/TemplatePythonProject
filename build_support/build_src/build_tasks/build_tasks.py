"""build_tasks should house all tasks that build artifacts that will be pushed."""

from pathlib import Path

from build_tasks.env_setup_tasks import BuildProdEnvironment
from build_tasks.test_tasks import TestPypi, TestPythonStyle
from build_vars.docker_vars import DockerTarget, get_docker_command_for_image
from build_vars.file_and_dir_path_vars import get_dist_dir, get_temp_dist_dir
from dag_engine import TaskNode, concatenate_args, run_process


class BuildPypi(TaskNode):
    """Task for building PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure all python checks are passing and prod env exists."""
        return [
            TestPypi(),
            TestPythonStyle(),
            BuildProdEnvironment(),
        ]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds PyPi package."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "rm",
                    "-rf",
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "poetry",
                    "build",
                ]
            )
        )
        # Todo: clean this up once a new version of poetry supporting "-o" is released
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "mv",
                    get_temp_dist_dir(project_root=docker_project_root),
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )
