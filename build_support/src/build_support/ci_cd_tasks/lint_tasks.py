"""Should hold all tasks that perform automated formatting of code."""

from pathlib import Path

from build_support.ci_cd_tasks.env_setup_tasks import BuildDevEnvironment
from build_support.ci_cd_tasks.test_tasks import TestBuildSupport, TestPypi
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_all_python_folders,
    get_docker_command_for_image,
)
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class Lint(TaskNode):
    """Linting task."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the tasks that have to be run before linting the project.

        Returns:
            list[TaskNode]: A list of tasks required to lint project.
        """
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Lints all python files in project.

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
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
        """Gets the tasks that have to be run before running autoflake on the project.

        We must ensure that all domain specific tests are passing.  Autoflake can
        cause cascading rewrites if some code has errors.

        Returns:
            list[TaskNode]: A list of tasks required to lint project.
        """
        return [Lint(), TestPypi(), TestBuildSupport()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs autoflake on all python files.

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
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
