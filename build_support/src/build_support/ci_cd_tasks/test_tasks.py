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
    ProjectContext,
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
    get_test_report_args,
)
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class TestAll(TaskNode):
    """A collective test task used to test all elements of the project."""

    def required_tasks(self) -> list[TaskNode]:
        """Adds all required "subtests" to the DAG."""
        return [TestPypi(), TestBuildSupport(), TestPythonStyle()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Does nothing."""


class TestBuildSupport(TaskNode):
    """Runs tests to ensure the following.

    - Branch and version are coherent.
    - Readme hasn't been wildly reformatted unexpectedly.
    - All elements of the build pipeline are passing tests.
    """

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running tests."""
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs tests in the build_test folder."""
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
                    get_test_report_args(
                        project_root=docker_project_root,
                        test_context=ProjectContext.BUILD_SUPPORT,
                    ),
                    get_build_support_src_and_test(project_root=docker_project_root),
                ]
            )
        )


class TestPythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running style checks."""
        return [GetGitInfo(), BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Runs all stylistic checks on code."""
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
                    get_test_report_args(
                        project_root=docker_project_root,
                        test_context=ProjectContext.DOCUMENTATION_ENFORCEMENT,
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
                        test_context=ProjectContext.PYPI,
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
                        test_context=ProjectContext.PULUMI,
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
                        test_context=ProjectContext.BUILD_SUPPORT,
                    ),
                    "-r",
                    get_build_support_src_dir(project_root=docker_project_root),
                ]
            )
        )


class TestPypi(TaskNode):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures dev env is built."""
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Tests the PyPi package."""
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
                    get_test_report_args(
                        project_root=docker_project_root,
                        test_context=ProjectContext.PYPI,
                    ),
                    get_pypi_src_and_test(project_root=docker_project_root),
                ]
            )
        )
