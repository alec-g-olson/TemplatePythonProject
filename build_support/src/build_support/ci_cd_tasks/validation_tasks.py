"""Should hold all tasks that run tests, both on artifacts and style tests.

Attributes:
    | FEATURE_TEST_FILE_NAME_REGEX: A regex for getting feature test file names.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import override

from junitparser import JUnitXml

from build_support.ci_cd_tasks.env_setup_tasks import (
    GetGitInfo,
    GitInfo,
    SetupDevEnvironment,
)
from build_support.ci_cd_tasks.task_node import PerSubprojectTask, TaskNode
from build_support.ci_cd_vars.build_paths import get_git_info_yaml
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
from build_support.file_caching import FileCacheEngine
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


def get_subprojects_to_test(project_root: Path) -> list[SubprojectContext]:
    """Gets the list of subprojects that should be tested.

    If the Dockerfile has been updated or the python dependencies have been updated
    then all subprojects should be tested.

    Args:
        project_root (Path): The path to this project's root.

    Returns:
        list[SubprojectContext]: The list of subprojects that should be tested.
    """
    git_info = GitInfo.from_yaml(
        get_git_info_yaml(project_root=project_root).read_text()
    )
    if git_info.dockerfile_modified or git_info.poetry_lock_file_modified:
        return get_sorted_subproject_contexts()
    return git_info.modified_subprojects


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


@dataclass
class UnitTestInfo:
    """A dataclass for organizing unit test information."""

    src_file_path: Path
    test_file_path: Path


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

    def get_unit_tests_to_run(
        self, file_cache: FileCacheEngine
    ) -> Iterator[UnitTestInfo]:
        """Gets information required to run unit tests.

        Args:
            file_cache (FileCacheEngine): The file cache that holds up-to-date
                information on which tests have passed and which haven't.

        Yields:
            Iterator[UnitTestInfo]: Generator of unit test info for tests that need to
                run.
        """
        for src_file, test_file in self.subproject.get_src_unit_test_file_pairs():
            if test_file.exists():
                most_recent_conftest_update = file_cache.most_recent_conftest_update(
                    test_dir=test_file.parent
                )
                src_file_updated = FileCacheEngine.get_last_modified_time(
                    file_path=src_file
                )
                test_file_updated = FileCacheEngine.get_last_modified_time(
                    file_path=test_file
                )
                test_file_info = file_cache.get_test_info_for_file(file_path=test_file)
                if (
                    test_file_info.tests_passed is None
                    or test_file_info.tests_passed < src_file_updated
                    or test_file_info.tests_passed < test_file_updated
                    or test_file_info.tests_passed < most_recent_conftest_update
                ):
                    yield UnitTestInfo(src_file_path=src_file, test_file_path=test_file)
            else:
                msg = f"Expected {test_file} to exist!"
                raise ValueError(msg)

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can unit test the subproject.

        Returns:
            list[TaskNode]: A list of tasks required to unit test the subproject.
        """
        required_tasks: list[TaskNode] = [
            SetupDevEnvironment(basic_task_info=self.get_basic_task_info()),
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
        ]
        return required_tasks

    @override
    def run(self) -> None:
        """Runs unit tests for the subproject.

        Returns:
            None
        """
        if self.subproject_context not in get_subprojects_to_test(
            project_root=self.docker_project_root
        ):
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
        src_files_tested = 0
        for unit_test_info in self.get_unit_tests_to_run(file_cache=file_cache):
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
                file_path=unit_test_info.test_file_path
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


FEATURE_TEST_FILE_NAME_REGEX = re.compile(r"test_.+_.+\.py")


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
            GetGitInfo(basic_task_info=self.get_basic_task_info()),
            SubprojectUnitTests(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=self.subproject_context,
            ),
        ]
        if self.subproject_context == SubprojectContext.BUILD_SUPPORT:
            required_tasks.extend(
                [
                    ValidatePythonStyle(basic_task_info=self.get_basic_task_info()),
                    EnforceProcess(basic_task_info=self.get_basic_task_info()),
                ]
            )
        return required_tasks

    def get_feature_tests_to_run(self, file_cache: FileCacheEngine) -> Iterator[Path]:
        """Gets information required to run feature tests.

        Args:
            file_cache (FileCacheEngine): The file cache that holds up-to-date
                information on which tests have passed and which haven't.

        Returns:
            FeatureTestInfo: A dataclass with the cache information for feature tests.
        """
        feature_test_dir = self.subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        )
        most_recent_conftest_update = file_cache.most_recent_conftest_update(
            test_dir=feature_test_dir
        )
        most_recent_src_file_update = file_cache.most_recent_src_file_update()

        test_files = [
            file
            for file in feature_test_dir.glob("*")
            if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
        ]

        # Update feature test file timestamps
        for test_file in test_files:
            test_file_info = file_cache.get_test_info_for_file(file_path=test_file)
            if (
                test_file_info.tests_passed is None
                or test_file_info.tests_passed < most_recent_conftest_update
                or test_file_info.tests_passed < most_recent_src_file_update
            ):
                yield test_file

    @override
    def run(self) -> None:
        """Runs feature tests for the subproject.

        Returns:
            None
        """
        if self.subproject_context not in get_subprojects_to_test(
            project_root=self.docker_project_root
        ):
            return
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

        complete_xml_path = self.subproject.get_pytest_report_path(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS,
            test_scope=PythonSubproject.TestScope.COMPLETE,
        )
        incomplete_xml_path = self.subproject.get_pytest_report_path(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS,
            test_scope=PythonSubproject.TestScope.INCOMPLETE,
        )

        for feature_test_path in self.get_feature_tests_to_run(file_cache=file_cache):
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
                        feature_test_path,
                    ]
                )
            )
            single_file_xml_path = self.subproject.get_pytest_report_path(
                test_suite=PythonSubproject.TestSuite.FEATURE_TESTS,
                test_scope=PythonSubproject.TestScope.SINGLE_FILE,
            )
            if incomplete_xml_path.exists():
                incomplete_xml_results = JUnitXml.fromfile(str(incomplete_xml_path))
                single_file_xml_results = JUnitXml.fromfile(str(single_file_xml_path))
                incomplete_xml_results += single_file_xml_results
                incomplete_xml_results.write()
            else:
                single_file_xml_path.rename(incomplete_xml_path)
            # Record that the feature test passed
            file_cache.update_test_pass_timestamp(file_path=feature_test_path)
            file_cache.write_text()

        if (
            incomplete_xml_path.exists() and not complete_xml_path.exists()
        ):  # pragma: no cov
            incomplete_xml_path.rename(complete_xml_path)
