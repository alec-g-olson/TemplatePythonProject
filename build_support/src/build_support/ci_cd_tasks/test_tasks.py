"""Should hold all tasks that run tests, both on artifacts and style tests."""

from pathlib import Path

from build_support.ci_cd_tasks.env_setup_tasks import BuildDevEnvironment, GetGitInfo
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_all_python_folders,
    get_base_docker_command_for_image,
    get_build_support_src_dir,
    get_docker_command_for_image,
    get_docker_image_name,
    get_mypy_path_env,
    get_pulumi_dir,
    get_pypi_src_dir,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    SubprojectContext,
    get_all_src_folders,
    get_all_test_folders,
    get_build_support_src_and_test,
    get_build_support_test_dir,
    get_documentation_tests_dir,
    get_pypi_src_and_test,
)
from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE
from build_support.ci_cd_vars.python_vars import (
    get_bandit_report_path,
    get_pytest_report_args,
)
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class TestAll(TaskNode):
    """A collective test task used to test all elements of the project."""

    def required_tasks(self) -> list[TaskNode]:
        """Lists all "subtests" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [TestPypi(), TestBuildSupport(), TestPythonStyle()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Does nothing.

        Arguments are inherited from sub-class.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """


class TestBuildSupport(TaskNode):
    """Runs tests to ensure all elements of the build pipeline are passing tests."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test the build pipeline.

        Returns:
            list[TaskNode]: A list of tasks required to test the build pipeline.
        """
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs tests in the build_support/test folder.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.BUILD_SUPPORT,
                    ),
                    get_build_support_src_and_test(project_root=docker_project_root),
                ]
            )
        )


class TestPythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code and project version."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test python style.

        Returns:
            list[TaskNode]: A list of tasks required to test python style.
        """
        return [GetGitInfo(), BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs all stylistic checks on code.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
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
                    "--check-only",
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
                    "--check",
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
                    "pydocstyle",
                    get_all_src_folders(project_root=docker_project_root),
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
                    "pydocstyle",
                    "--add-ignore=D100,D104",
                    get_all_test_folders(project_root=docker_project_root),
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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
                    ),
                    get_documentation_tests_dir(project_root=docker_project_root),
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
                    "flake8",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=non_docker_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image_name(
                    project_root=docker_project_root, target_image=DockerTarget.DEV
                ),
                "mypy",
                "--explicit-package-bases",
            ]
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_pypi_src_and_test(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_build_support_src_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_build_support_test_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_pulumi_dir(project_root=docker_project_root),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.PYPI,
                    ),
                    "-r",
                    get_pypi_src_dir(project_root=docker_project_root),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.PULUMI,
                    ),
                    "-r",
                    get_pulumi_dir(project_root=docker_project_root),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.BUILD_SUPPORT,
                    ),
                    "-r",
                    get_build_support_src_dir(project_root=docker_project_root),
                ]
            )
        )


class TestPypi(TaskNode):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test the pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to test the pypi package.
        """
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Tests the PyPi package.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=docker_project_root,
                        test_context=SubprojectContext.PYPI,
                    ),
                    get_pypi_src_and_test(project_root=docker_project_root),
                ]
            )
        )
