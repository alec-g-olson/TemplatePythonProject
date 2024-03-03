"""Should hold all tasks that perform automated formatting of code."""


from build_support.ci_cd_tasks.env_setup_tasks import SetupDevEnvironment
from build_support.ci_cd_tasks.validation_tasks import (
    ValidateBuildSupport,
    ValidatePypi,
)
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_all_python_folders,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_test_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.git_status_vars import commit_changes_if_diff
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class Lint(TaskNode):
    """Linting task."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the tasks that have to be run before linting the project.

        Returns:
            list[TaskNode]: A list of tasks required to lint project.
        """
        return [
            SetupDevEnvironment(
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
                    "ruff",
                    "check",
                    "--select",
                    "I",
                    "--fix",
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
                    "ruff",
                    "format",
                    get_all_python_folders(project_root=self.docker_project_root),
                ],
            ),
        )


class RuffFixSafe(TaskNode):
    """Task for running ruff check --fix on all python files in project."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the tasks to run before running ruff check --fix on the project.

        We must ensure that all domain specific tests are passing.  ruff check --fix
        should be safe, but if the code is incorrect cause cascading rewrites can occur.

        Returns:
            list[TaskNode]: A list of tasks required to safely fix code issues.
        """
        return [
            Lint(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
            ValidatePypi(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
            ValidateBuildSupport(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            ),
        ]

    def run(self) -> None:
        """Runs ruff check --fix on all python files.

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
                    "ruff",
                    "check",
                    "--fix",
                    get_all_non_test_folders(project_root=self.docker_project_root),
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
                    "ruff",
                    "check",
                    "--ignore",
                    "D",
                    "--fix",
                    get_all_test_folders(project_root=self.docker_project_root),
                ],
            ),
        )


class ApplyRuffFixUnsafe(TaskNode):
    """Task for running ruff check --fix --unsafe-fixes on all python files.

    This task requires safe fixes to be applied first, and the first thing done by this
    task is to commit any changes (including the safe fixes that had just been applied).
    Then unsafe fixes are attempted.
    """

    def required_tasks(self) -> list[TaskNode]:
        """Gets the tasks to run before running ruff check --fix --unsafe-fixes.

        Returns:
            list[TaskNode]: A list of tasks required to lint project.
        """
        return [
            RuffFixSafe(
                non_docker_project_root=self.non_docker_project_root,
                docker_project_root=self.docker_project_root,
                local_user_uid=self.local_user_uid,
                local_user_gid=self.local_user_gid,
            )
        ]

    def run(self) -> None:
        """Runs ruff check --fix on all python files.

        Returns:
            None
        """
        commit_changes_if_diff(
            commit_message_no_quotes=(
                "Committing staged changes for before applying unsafe ruff fixes."
            ),
            local_user_uid=self.local_user_uid,
            local_user_gid=self.local_user_gid,
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "ruff",
                    "check",
                    "--fix",
                    "--unsafe-fixes",
                    get_all_non_test_folders(project_root=self.docker_project_root),
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
                    "ruff",
                    "check",
                    "--ignore",
                    "D",
                    "--fix",
                    "--unsafe-fixes",
                    get_all_test_folders(project_root=self.docker_project_root),
                ],
            ),
        )
