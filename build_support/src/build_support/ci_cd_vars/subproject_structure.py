"""Defines the structure of a python subproject."""

from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.project_structure import get_build_dir, maybe_build_dir
from build_support.process_runner import concatenate_args


class SubprojectContext(StrEnum):
    """An Enum to track the python subprojects with similar structure."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    INFRA = "infra"


def get_sorted_subproject_contexts() -> list[SubprojectContext]:
    """List the subproject context enums in a repeatable manner.

    Returns:
        list[SubprojectContext]: A sorted list of subproject context enums.
    """
    return sorted(
        (subproject_context for subproject_context in SubprojectContext),
        key=lambda x: x.value,
    )


@dataclass(frozen=True)
class PythonSubproject:
    """Class that describes a python subproject."""

    project_root: Path
    subproject_context: SubprojectContext

    class TestSuite(Enum):
        """An Enum to track the possible test contexts."""

        UNIT_TESTS = "unit_tests"
        FEATURE_TESTS = "feature_tests"
        # The Enums below should only be used in the BUILD_SUPPORT subproject
        PROCESS_ENFORCEMENT = "process_enforcement"
        STYLE_ENFORCEMENT = "style_enforcement"

    class TestScope(Enum):
        """An Enum to track if the scope of a pytest call is complete for the suite."""

        COMPLETE = "complete"
        INCOMPLETE = "incomplete"
        SINGLE_FILE = "single_file"

    def get_subproject_name(self) -> str:
        """Gets the name of the subproject.

        Returns:
            str: The name of the subproject.
        """
        return self.subproject_context.value

    def get_build_dir(self) -> Path:
        """Gets and possibly builds a directory in the build folder for this subproject.

        Returns:
            Path: Path to the build dir for this subproject.
        """
        return maybe_build_dir(
            get_build_dir(project_root=self.project_root).joinpath(
                self.get_subproject_name()
            )
        )

    def get_reports_dir(self) -> Path:
        """Gets and possibly builds a dir for storing the subproject build reports.

        Returns:
            Path: Path to the subproject's reports directory.
        """
        return maybe_build_dir(self.get_build_dir().joinpath("reports"))

    def get_root_dir(self) -> Path:
        """Gets the root of the python subproject.

        Returns:
            Path: Path to the root of the python subproject.
        """
        return self.project_root.joinpath(self.get_subproject_name())

    def get_src_dir(self) -> Path:
        """Gets the src folder in a subproject.

        Returns:
            Path: Path to the src folder in the subproject.
        """
        return self.get_root_dir().joinpath("src")

    def get_python_package_dir(self) -> Path:
        """Gets the python package folder in a subproject.

        Returns:
            Path: Path to the python package folder in the subproject.
        """
        return self.get_src_dir().joinpath(
            self.subproject_context.value
            if self.subproject_context != SubprojectContext.PYPI
            else get_project_name(project_root=self.project_root)
        )

    def get_test_dir(self) -> Path:
        """Gets the test folder in a subproject.

        Returns:
            Path: Path to the test folder in the subproject.
        """
        return self.get_root_dir().joinpath("test")

    def get_test_suite_dir(self, test_suite: TestSuite) -> Path:
        """Gets the appropriate test suite folder in a subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                dir.

        Returns:
            Path: Path to the unit test folder in the subproject.
        """
        return self.get_test_dir().joinpath(test_suite.value)

    def _get_test_report_name(
        self, test_suite: TestSuite | None, report_extension: str
    ) -> str:
        """Enforces a consistent python report naming convention.

        Args:
            test_suite (TestSuite | None): The suite of tests we are running.
            report_extension (str): The end of the requested report's filename including
                the extension.

        Returns:
            str: The name of a pytest report in a standardized format.
        """
        return "_".join(
            x
            for x in (
                get_project_name(project_root=self.project_root),
                get_project_version(project_root=self.project_root),
                self.get_subproject_name(),
                test_suite.value if test_suite else None,
                report_extension,
            )
            if x
        )

    def get_bandit_report_name(self) -> str:
        """Get the name of the bandit security report for this project.

        Returns:
            str: The name of a bandit report in a standardized format.
        """
        return self._get_test_report_name(
            test_suite=None, report_extension="bandit_report.txt"
        )

    def get_bandit_report_path(self) -> Path:
        """Get the path of the infra bandit security report for this project.

        Returns:
            Path: Path to the bandit report for this subproject.
        """
        return self.get_reports_dir().joinpath(self.get_bandit_report_name())

    def get_pytest_report_name(
        self, test_suite: TestSuite, test_scope: TestScope
    ) -> str:
        """Get the name of the pytest report for this subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                we are getting the pytest report name for.
            test_scope (TestScope): The test scope enum indicating how complete the test
                call will be for the test suite.

        Returns:
            str: The name of a pytest report in a standardized format.
        """
        if test_scope == PythonSubproject.TestScope.COMPLETE:
            return self._get_test_report_name(
                test_suite=test_suite, report_extension="pytest_report.xml"
            )
        return self._get_test_report_name(
            test_suite=test_suite,
            report_extension=f"pytest_report_{test_scope.value}.xml",
        )

    def get_pytest_report_path(
        self, test_suite: TestSuite, test_scope: TestScope
    ) -> Path:
        """Get the path of the pytest report for this subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                we are getting the pytest report path for.
            test_scope (TestScope): The test scope enum indicating how complete the test
                call will be for the test suite.

        Returns:
            Path: Path to the pytest report for this subproject.
        """
        return self.get_reports_dir().joinpath(
            self.get_pytest_report_name(test_suite=test_suite, test_scope=test_scope)
        )

    def get_pytest_coverage_report_name(self, test_suite: TestSuite) -> str:
        """Get the name of the pytest coverage report for this subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                we are getting the pytest coverage report name for.

        Returns:
            str: The name of a pytest coverage report in a standardized format.
        """
        return self._get_test_report_name(
            test_suite=test_suite, report_extension="pytest_coverage_report.xml"
        )

    def get_pytest_coverage_report_path(self, test_suite: TestSuite) -> Path:
        """Get the path of the pytest coverage report for this subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                we are getting the pytest coverage report path for.

        Returns:
            Path: Path to the pytest coverage report for this subproject.
        """
        return self.get_reports_dir().joinpath(
            self.get_pytest_coverage_report_name(test_suite=test_suite)
        )

    def get_pytest_whole_test_suite_report_args(
        self, test_suite: TestSuite
    ) -> list[str]:
        """Get the args used by pytest when running test suites for this subproject.

        Args:
            test_suite (TestSuite): The test suite enum corresponding to the test suite
                we are getting report args for.

        Returns:
            list[str]: A list of arguments that will be used with pytest when running
                unit tests for this subproject.
        """
        report_path = self.get_pytest_report_path(
            test_suite=test_suite, test_scope=PythonSubproject.TestScope.COMPLETE
        )
        report_args: list[Any] = [
            # Always check to make sure all test code is covered
            # It's a good check to make sure we're doing what we expect with our tests
            "--cov-report",
            "term-missing",
            f"--cov={self.get_test_suite_dir(test_suite=test_suite)}",
            f"--junitxml={report_path}",
        ]
        if test_suite == self.TestSuite.UNIT_TESTS:
            coverage_report = self.get_pytest_coverage_report_path(
                test_suite=test_suite
            )
            report_args.extend(
                (f"--cov={self.get_src_dir()}", f"--cov-report=xml:{coverage_report}")
            )
        return concatenate_args(args=report_args)

    def get_pytest_feature_test_report_args(self) -> list[str]:
        """Get the args used by pytest when running features tests for this subproject.

        Returns:
            list[str]: A list of arguments that will be used with pytest when running
                feature tests for this subproject.
        """
        report_path = self.get_pytest_report_path(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS,
            test_scope=PythonSubproject.TestScope.SINGLE_FILE,
        )
        return [f"--junitxml={report_path}"]

    def get_file_cache_yaml(self) -> Path:
        """Gets the file that holds this subproject's file cache information.

        Returns:
            Path: Path to this subproject's file cache info.
        """
        return self.get_build_dir().joinpath("file_cache.yaml")


def get_python_subproject(
    subproject_context: SubprojectContext, project_root: Path
) -> PythonSubproject:
    """Gets a Python subproject.

    Args:
        subproject_context (SubprojectContext): An Enum specifying which python
            subproject to get.
        project_root (Path): The root directory of the project.

    Returns:
        PythonSubproject: A dataclass that dictates the structure a python subproject.
    """
    return PythonSubproject(
        project_root=project_root, subproject_context=subproject_context
    )


def get_all_python_subprojects_dict(
    project_root: Path,
) -> dict[SubprojectContext, PythonSubproject]:
    """Gets all Python subprojects in a dict.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        dict[SubprojectContext, PythonSubproject]: A dict of all Python subprojects
            using their SubprojectContext as a key.
    """
    return {
        subproject_context: PythonSubproject(
            project_root=project_root, subproject_context=subproject_context
        )
        for subproject_context in SubprojectContext
    }


def get_all_python_subprojects_with_src(project_root: Path) -> list[PythonSubproject]:
    """Gets all Python subprojects that have a src folder.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        list[PythonSubproject]: A list of all Python subprojects with a src dir.
    """
    return [
        subproject
        for subproject in (
            PythonSubproject(
                project_root=project_root, subproject_context=subproject_context
            )
            for subproject_context in get_sorted_subproject_contexts()
        )
        if subproject.get_src_dir().exists()
    ]


def get_all_python_subprojects_with_test(project_root: Path) -> list[PythonSubproject]:
    """Gets all Python subprojects that have a test folder.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        list[PythonSubproject]: A list of all Python subprojects with a test dir.
    """
    return [
        subproject
        for subproject in (
            PythonSubproject(
                project_root=project_root, subproject_context=subproject_context
            )
            for subproject_context in get_sorted_subproject_contexts()
        )
        if subproject.get_test_dir().exists()
    ]
