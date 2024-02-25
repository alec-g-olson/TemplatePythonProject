"""Should hold all tasks that perform automated formatting of code."""


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
        return [
            BuildDevEnvironment(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
        ]

    def run(self) -> None:
        """Lints all python files in project.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "isort",
                    get_all_python_folders(project_root=self.docker_project_root),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "black",
                    get_all_python_folders(project_root=self.docker_project_root),
                ],
            ),
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
        return [
            Lint(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
            TestPypi(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
            TestBuildSupport(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
        ]

    def run(self) -> None:
        """Runs autoflake on all python files.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--remove-duplicate-keys",
                    "--in-place",
                    "--recursive",
                    get_all_python_folders(project_root=self.docker_project_root),
                ],
            ),
        )
