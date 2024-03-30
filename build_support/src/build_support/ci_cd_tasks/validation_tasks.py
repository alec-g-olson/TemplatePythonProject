"""Should hold all tasks that run tests, both on artifacts and style tests."""

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
from build_support.ci_cd_tasks.task_node import PerSubprojectTask, TaskNode
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
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_sorted_subproject_contexts,
)
from build_support.file_caching import FileCacheInfo
from build_support.process_runner import concatenate_args, run_process


class ValidateAll(TaskNode):
    """A collective test task used to test all elements of the project."""

    def required_tasks(self) -> list[TaskNode]:
        """Lists all "subtests" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [
            AllSubprojectUnitTests(basic_task_info=self.get_basic_task_info()),
            ValidatePythonStyle(basic_task_info=self.get_basic_task_info()),
        ]

    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


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
                    "D,FBT",  # These are too onerous to enforce on test code
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
                    subproject[
                        SubprojectContext.DOCUMENTATION_ENFORCEMENT
                    ].get_pytest_report_args(),
                    subproject[
                        SubprojectContext.DOCUMENTATION_ENFORCEMENT
                    ].get_test_dir(),
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
                    subproject[SubprojectContext.PYPI].get_root_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[
                        SubprojectContext.DOCUMENTATION_ENFORCEMENT
                    ].get_root_dir(),
                ],
            ),
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    subproject[SubprojectContext.INFRA].get_root_dir(),
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
                    subproject[SubprojectContext.PYPI].get_bandit_report_path(),
                    "-r",
                    subproject[SubprojectContext.PYPI].get_src_dir(),
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
                    subproject[SubprojectContext.INFRA].get_bandit_report_path(),
                    "-r",
                    subproject[SubprojectContext.INFRA].get_src_dir(),
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
                    subproject[
                        SubprojectContext.BUILD_SUPPORT
                    ].get_bandit_report_path(),
                    "-r",
                    subproject[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
                ],
            ),
        )


class AllSubprojectUnitTests(TaskNode):
    """Task for running unit tests in all subprojects."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the subproject specific unit test tasks.

        Returns:
            list[TaskNode]: All the subproject specific unit test tasks.
        """
        return [
            SubprojectUnitTests(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=subproject_context,
            )
            for subproject_context in get_sorted_subproject_contexts()
        ]

    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class SubprojectUnitTests(PerSubprojectTask):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can test the pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to test the pypi package.
        """
        required_tasks: list[TaskNode] = [
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]
        if self.subproject_context == SubprojectContext.BUILD_SUPPORT:
            required_tasks.append(
                GetGitInfo(basic_task_info=self.get_basic_task_info())
            )
        return required_tasks

    def run(self) -> None:
        """Tests the PyPi package.

        Returns:
            None
        """
        dev_docker_command = get_docker_command_for_image(
            non_docker_project_root=self.non_docker_project_root,
            docker_project_root=self.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        src_root = self.subproject.get_python_package_dir()
        if src_root.exists():
            subproject_root = self.subproject.get_root_dir()
            unit_test_cache_file = self.subproject.get_unit_test_cache_yaml()
            if unit_test_cache_file.exists():
                unit_test_cache = FileCacheInfo.from_yaml(
                    unit_test_cache_file.read_text()
                )
            else:
                unit_test_cache = FileCacheInfo(
                    group_root_dir=subproject_root, cache_info={}
                )
            unit_test_root = self.subproject.get_unit_test_dir()
            src_files = sorted(src_root.rglob("*"))
            src_files_checked = 0
            for src_file in src_files:
                if (
                    src_file.is_file()
                    and src_file.name.endswith(".py")
                    and src_file.name != "__init__.py"
                ):
                    relative_path = src_file.relative_to(src_root)
                    test_folder = unit_test_root.joinpath(relative_path).parent
                    test_file = test_folder.joinpath(f"test_{src_file.name}")
                    src_changed = unit_test_cache.file_has_been_changed(
                        file_path=src_file
                    )
                    test_changed = unit_test_cache.file_has_been_changed(
                        file_path=test_file
                    )
                    # evaluate file change before if to ensure they are updated in the
                    # file cache data.  Otherwise, if src is different then test is not
                    # checked and will stay stale until this code is run again.
                    if src_changed or test_changed:
                        src_files_checked += 1
                        run_process(
                            args=concatenate_args(
                                args=[
                                    dev_docker_command,
                                    "coverage",
                                    "run",
                                    "--include",
                                    src_file,
                                    "-m",
                                    "pytest",
                                    test_file,
                                ],
                            ),
                        )
                        run_process(
                            args=concatenate_args(
                                args=[
                                    dev_docker_command,
                                    "coverage",
                                    "report",
                                    "-m",
                                ],
                            ),
                        )
                    unit_test_cache_file.write_text(unit_test_cache.to_yaml())
            if src_files_checked:
                run_process(
                    args=concatenate_args(
                        args=[
                            dev_docker_command,
                            "pytest",
                            "-n",
                            THREADS_AVAILABLE,
                            self.subproject.get_pytest_report_args(),
                            self.subproject.get_src_and_test_dir(),
                        ],
                    ),
                )
