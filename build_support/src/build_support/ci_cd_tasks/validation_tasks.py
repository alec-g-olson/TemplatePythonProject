"""Should hold all tasks that run tests, both on artifacts and style tests."""

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_base_docker_command_for_image,
    get_docker_command_for_image,
    get_docker_image_name,
    get_mypy_path_env,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_test_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE
from build_support.ci_cd_vars.python_vars import (
    get_bandit_report_path,
    get_pytest_report_args,
)
from build_support.ci_cd_vars.subproject_enum import SubprojectContext
from build_support.ci_cd_vars.subproject_structure import (
    get_all_python_subprojects_dict,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args, run_process


class ValidateAll(TaskNode):
    """A collective test task used to test all elements of the project."""

    def required_tasks(self) -> list[TaskNode]:
        """Lists all "subtests" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [
            ValidatePypi(basic_task_info=self.get_basic_task_info()),
            ValidateBuildSupport(basic_task_info=self.get_basic_task_info()),
            ValidatePythonStyle(basic_task_info=self.get_basic_task_info()),
        ]

    def run(self) -> None:
        """Does nothing.

        Arguments are inherited from subclass.

        Returns:
            None
        """


class ValidateBuildSupport(TaskNode):
    """Runs tests to ensure all elements of the build pipeline are passing tests."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can test the build pipeline.

        Returns:
            list[TaskNode]: A list of tasks required to test the build pipeline.
        """
        # Needs git info to tell if we are on main for some tests that could go stale
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    def run(self) -> None:
        """Runs tests in the build_support/test folder.

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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.BUILD_SUPPORT,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    get_python_subproject(
                        subproject_context=SubprojectContext.BUILD_SUPPORT,
                        project_root=self.docker_project_root,
                    ).get_subproject_src_and_test_dir(),
                ],
            ),
        )


class ValidatePythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code and project version."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test python style.

        Returns:
            list[TaskNode]: A list of tasks required to test python style.
        """
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    def run(self) -> None:
        """Runs all stylistic checks on code.

        Returns:
            None
        """
        subproject = get_all_python_subprojects_dict(
            project_root=self.docker_project_root
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
                    get_all_test_folders(project_root=self.docker_project_root),
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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    subproject[
                        SubprojectContext.DOCUMENTATION_ENFORCEMENT
                    ].get_subproject_test_dir(),
                ],
            ),
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=self.non_docker_project_root,
                    docker_project_root=self.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=self.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image_name(
                    project_root=self.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "mypy",
                "--explicit-package-bases",
            ],
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[SubprojectContext.PYPI].get_subproject_root(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[
                        SubprojectContext.BUILD_SUPPORT
                    ].get_subproject_src_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[
                        SubprojectContext.BUILD_SUPPORT
                    ].get_subproject_test_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[
                        SubprojectContext.DOCUMENTATION_ENFORCEMENT
                    ].get_subproject_root(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[SubprojectContext.PULUMI].get_subproject_root(),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.PYPI,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    "-r",
                    subproject[SubprojectContext.PYPI].get_subproject_src_dir(),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.PULUMI,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    "-r",
                    subproject[SubprojectContext.PULUMI].get_subproject_root(),
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
                    "bandit",
                    "-o",
                    get_bandit_report_path(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.BUILD_SUPPORT,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    "-r",
                    subproject[
                        SubprojectContext.BUILD_SUPPORT
                    ].get_subproject_src_dir(),
                ],
            ),
        )


class ValidatePypi(TaskNode):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can test the pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to test the pypi package.
        """
        return [
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    def run(self) -> None:
        """Tests the PyPi package.

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
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_pytest_report_args(
                        project_root=self.docker_project_root,
                        subproject=get_python_subproject(
                            subproject_context=SubprojectContext.PYPI,
                            project_root=self.docker_project_root,
                        ),
                    ),
                    get_python_subproject(
                        subproject_context=SubprojectContext.PYPI,
                        project_root=self.docker_project_root,
                    ).get_subproject_src_and_test_dir(),
                ],
            ),
        )
