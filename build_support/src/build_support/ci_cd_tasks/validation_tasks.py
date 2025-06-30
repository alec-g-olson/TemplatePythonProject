"""Should hold all tasks that run tests, both on artifacts and style tests."""

from pathlib import Path
from typing import override

from junitparser import JUnitXml

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
from build_support.ci_cd_vars.project_structure import get_feature_test_scratch_folder
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
    get_sorted_subproject_contexts,
)
from build_support.file_caching import FileCacheEngine, ParentConftestStatus
from build_support.process_runner import concatenate_args, run_process


class ValidateAll(TaskNode):
    """A collective test task used to test all elements of the project."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Lists all "subtests" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        basic_task_info = self.get_basic_task_info()
        return [
            AllSubprojectUnitTests(basic_task_info=basic_task_info),
            ValidatePythonStyle(basic_task_info=basic_task_info),
            AllSubprojectStaticTypeChecking(basic_task_info=basic_task_info),
            AllSubprojectSecurityChecks(basic_task_info=basic_task_info),
            EnforceProcess(basic_task_info=basic_task_info),
            AllSubprojectFeatureTests(basic_task_info=basic_task_info),
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class EnforceProcess(TaskNode):
    """Task enforces the team's agreed build process for this project."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before enforcing the build process.

        Returns:
            list[TaskNode]: A list of tasks required to enforce the build process.
        """
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Runs tests that enforce the build process.

        Returns:
            None
        """
        build_support_subproject = get_python_subproject(
            subproject_context=SubprojectContext.BUILD_SUPPORT,
            project_root=self.docker_project_root,
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
                    build_support_subproject.get_pytest_whole_test_suite_report_args(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                    build_support_subproject.get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                ]
            )
        )


class AllSubprojectStaticTypeChecking(TaskNode):
    """Task for running static type checking in all subprojects."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the subproject specific static type checking tasks.

        Returns:
            list[TaskNode]: All the subproject specific static type checking tasks.
        """
        return [
            ValidateStaticTypeChecking(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=subproject_context,
            )
            for subproject_context in get_sorted_subproject_contexts()
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class ValidateStaticTypeChecking(PerSubprojectTask):
    """Task for enforcing static type checking."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test type checks.

        Returns:
            list[TaskNode]: A list of tasks required to do static type checking.
        """
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Runs all static type checks on subproject.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(
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
                    self.subproject.get_root_dir(),
                ]
            )
        )


class AllSubprojectSecurityChecks(TaskNode):
    """Task for running static security checking in all subprojects."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the subproject specific security type checking tasks.

        Returns:
            list[TaskNode]: All the subproject specific security type checking tasks.
        """
        return [
            ValidateSecurityChecks(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=subproject_context,
            )
            for subproject_context in get_sorted_subproject_contexts()
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class ValidateSecurityChecks(PerSubprojectTask):
    """Task for enforcing static security checking."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test security checks.

        Returns:
            list[TaskNode]: A list of tasks required to do static security checking.
        """
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Runs security checks on subproject.

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
                    "bandit",
                    "-o",
                    self.subproject.get_bandit_report_path(),
                    "-r",
                    self.subproject.get_src_dir(),
                ]
            )
        )


class ValidatePythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code and project version."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks that need to be run before we can test python style.

        Returns:
            list[TaskNode]: A list of tasks required to test python style.
        """
        return [
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    @override
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
                ]
            )
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
                ]
            )
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
                        SubprojectContext.BUILD_SUPPORT
                    ].get_pytest_whole_test_suite_report_args(
                        test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                    ),
                    subproject[SubprojectContext.BUILD_SUPPORT].get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                    ),
                ]
            )
        )


class AllSubprojectUnitTests(TaskNode):
    """Task for running unit tests in all subprojects."""

    @override
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

    @override
    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class SubprojectUnitTests(PerSubprojectTask):
    """Task for running unit tests in a single subproject."""

    @staticmethod
    def get_module_from_path(src_file_path: Path, subproject: PythonSubproject) -> str:
        """Gets the module name from a path.

        Args:
            src_file_path (Path): The path to the source file.
            subproject (PythonSubproject): The subproject the source file is in.

        Returns:
            str: The module name.
        """
        src_root = subproject.get_src_dir()
        relative_path = src_file_path.relative_to(src_root)
        relative_path_ext_stripped = relative_path.with_suffix("")
        return ".".join(relative_path_ext_stripped.parts)

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can unit test the subproject.

        Returns:
            list[TaskNode]: A list of tasks required to unit test the subproject.
        """
        required_tasks: list[TaskNode] = [
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info())
        ]
        if self.subproject_context == SubprojectContext.BUILD_SUPPORT:
            required_tasks.append(
                GetGitInfo(basic_task_info=self.get_basic_task_info())
            )
        return required_tasks

    @override
    def run(self) -> None:
        """Runs unit tests for the subproject.

        Returns:
            None
        """
        dev_docker_command = get_docker_command_for_image(
            non_docker_project_root=self.non_docker_project_root,
            docker_project_root=self.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        file_cache = FileCacheEngine(
            subproject_context=self.subproject_context,
            project_root=self.docker_project_root,
        )
        src_files_tested = 0
        for unit_test_info in file_cache.get_unit_tests_to_run():
            src_files_tested += 1
            src_module = SubprojectUnitTests.get_module_from_path(
                src_file_path=unit_test_info.src_file_path, subproject=self.subproject
            )
            run_process(
                args=concatenate_args(
                    args=[
                        dev_docker_command,
                        "pytest",
                        "-n",
                        THREADS_AVAILABLE,
                        "--cov-report",
                        "term-missing",
                        f"--cov={src_module}",
                        unit_test_info.test_file_path,
                    ]
                )
            )
            file_cache.update_test_pass_timestamp(
                file_path=unit_test_info.test_file_path,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST_SUCCESS,
            )
            file_cache.write_text()
        if src_files_tested:
            run_process(
                args=concatenate_args(
                    args=[
                        dev_docker_command,
                        "pytest",
                        "-n",
                        THREADS_AVAILABLE,
                        self.subproject.get_pytest_whole_test_suite_report_args(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                        self.subproject.get_src_dir(),
                        self.subproject.get_test_suite_dir(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                    ]
                )
            )

            # Conftest and file timestamps are already updated by get_unit_test_info()
            file_cache.write_text()


class AllSubprojectFeatureTests(TaskNode):
    """Task for running feature tests in all subprojects."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the subproject specific feature test tasks.

        Returns:
            list[TaskNode]: All the subproject specific feature test tasks.
        """
        return [
            SubprojectFeatureTests(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=subproject_context,
            )
            for subproject_context in get_sorted_subproject_contexts()
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Returns:
            None
        """


class SubprojectFeatureTests(PerSubprojectTask):
    """Task for running feature tests in a single subproject."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can feature test the subproject.

        Most of our build process feature tests will break if style and process
        checks fail.  So we want to make sure that our style and process tests are
        passing before running build support feature tests.

        Returns:
            list[TaskNode]: A list of tasks required to feature test the subproject.
        """
        required_tasks: list[TaskNode] = [
            SubprojectUnitTests(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=self.subproject_context,
            )
        ]
        if self.subproject_context == SubprojectContext.BUILD_SUPPORT:
            required_tasks.extend(
                [
                    ValidatePythonStyle(basic_task_info=self.get_basic_task_info()),
                    EnforceProcess(basic_task_info=self.get_basic_task_info()),
                ]
            )
        return required_tasks

    @override
    def run(self) -> None:
        """Runs feature tests for the subproject.

        Returns:
            None
        """
        if (
            self.ci_cd_feature_test_mode
            and self.subproject_context == SubprojectContext.BUILD_SUPPORT
        ):
            # prevents recursive calls to feature testing
            return
        dev_docker_command = get_docker_command_for_image(
            non_docker_project_root=self.non_docker_project_root,
            docker_project_root=self.docker_project_root,
            target_image=DockerTarget.DEV,
        )

        file_cache = FileCacheEngine(
            subproject_context=self.subproject_context,
            project_root=self.docker_project_root,
        )
        feature_test_info = file_cache.get_feature_test_info()
        run_all = (
            feature_test_info.conftest_or_parent_conftest_was_updated
            == ParentConftestStatus.UPDATED
            or any(
                file_cache.file_has_been_changed_since_last_timestamp_update(
                    file_path=src_file,
                    cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
                )
                for src_file in feature_test_info.src_files
            )
        )
        print("----------------------------------")  # noqa: T201
        print(feature_test_info.conftest_or_parent_conftest_was_updated)  # noqa: T201
        print(  # noqa: T201
            any(
                file_cache.file_has_been_changed_since_last_timestamp_update(
                    file_path=src_file,
                    cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
                )
                for src_file in feature_test_info.src_files
            )
        )
        for src_file in feature_test_info.src_files:
            updated = file_cache.file_has_been_changed_since_last_timestamp_update(
                file_path=src_file,
                cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
            )
            print(f"{updated}: {src_file}")  # noqa: T201
        print(run_all)  # noqa: T201
        print("----------------------------------")  # noqa: T201
        if run_all:
            test_files_to_run = sorted(feature_test_info.test_files)
        else:
            test_files_to_run = sorted(
                test_file
                for test_file in feature_test_info.test_files
                if file_cache.file_has_been_changed_since_last_timestamp_update(
                    file_path=test_file,
                    cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
                )
            )
        print("----------------------------------")  # noqa: T201
        print("Running:")  # noqa: T201
        for test_file in test_files_to_run:
            print(test_file)  # noqa: T201
        print(test_files_to_run)  # noqa: T201
        print("----------------------------------")  # noqa: T201
        test_suite = PythonSubproject.TestSuite.FEATURE_TESTS
        complete_xml_path = self.subproject.get_pytest_report_path(
            test_suite=test_suite, test_scope=PythonSubproject.TestScope.COMPLETE
        )
        incomplete_xml_path = self.subproject.get_pytest_report_path(
            test_suite=test_suite, test_scope=PythonSubproject.TestScope.INCOMPLETE
        )
        if test_files_to_run:
            for test_file_to_run in test_files_to_run:
                run_process(
                    args=concatenate_args(
                        args=[
                            dev_docker_command,
                            "pytest",
                            "--basetemp",
                            get_feature_test_scratch_folder(
                                project_root=self.docker_project_root
                            ),
                            self.subproject.get_pytest_feature_test_report_args(),
                            test_file_to_run,
                        ]
                    )
                )
                single_file_xml_path = self.subproject.get_pytest_report_path(
                    test_suite=test_suite,
                    test_scope=PythonSubproject.TestScope.SINGLE_FILE,
                )
                if incomplete_xml_path.exists():
                    incomplete_xml_results = JUnitXml.fromfile(str(incomplete_xml_path))
                    single_file_xml_results = JUnitXml.fromfile(
                        str(single_file_xml_path)
                    )
                    incomplete_xml_results += single_file_xml_results
                    incomplete_xml_results.write()
                else:
                    single_file_xml_path.rename(incomplete_xml_path)
                # Record that the feature test passed
                file_cache.update_test_pass_timestamp(
                    file_path=test_file_to_run,
                    cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST_SUCCESS,
                )
                file_cache.write_text()
            incomplete_xml_path.rename(complete_xml_path)

        if (
            incomplete_xml_path.exists() and not complete_xml_path.exists()
        ):  # pragma: no cov
            incomplete_xml_path.rename(complete_xml_path)
