"""Should hold all tasks that perform automated formatting of code."""

from pathlib import Path

from build_tasks.env_setup_tasks import BuildDevEnvironment
from build_tasks.test_tasks import TestBuildSanity, TestPypi
from build_vars.docker_vars import (
    DockerTarget,
    get_all_python_folders,
    get_docker_command_for_image,
)
from dag_engine import TaskNode, concatenate_args, run_process


class Lint(TaskNode):
    """Linting task."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure dev environment has been built before linting."""
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Lints all python files in project."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "isort",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "black",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )


class Autoflake(TaskNode):
    """Task for running autoflake on all python files in project."""

    def required_tasks(self) -> list[TaskNode]:
        """Run required tasks, including domain specific tests.

        We must ensure that all domain specific tests are passing.
        Autoflake can cause cascading rewrites if some code has errors.
        """
        return [Lint(), TestPypi(), TestBuildSanity()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs autoflake on all python files."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--remove-duplicate-keys",
                    "--in-place",
                    "--recursive",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
