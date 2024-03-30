"""Defines the structure of a python subproject."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.project_structure import get_build_dir, maybe_build_dir
from build_support.process_runner import concatenate_args


class SubprojectContext(Enum):
    """An Enum to track the possible docker targets and images."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    INFRA = "infra"
    DOCUMENTATION_ENFORCEMENT = "process_and_style_enforcement"


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

    def get_unit_test_dir(self) -> Path:
        """Gets the unit test folder in a subproject.

        Returns:
            Path: Path to the unit test folder in the subproject.
        """
        return self.get_test_dir().joinpath("unit_tests")

    def get_integration_test_dir(self) -> Path:
        """Gets the integration test folder in a subproject.

        Returns:
            Path: Path to the integration test folder in the subproject.
        """
        return self.get_test_dir().joinpath("integration_tests")

    def get_src_and_test_dir(self) -> list[Path]:
        """Gets the src and test dirs for the subproject.

        Returns:
            list[path]: Path to the build_support src and test dirs for the project.
        """
        return [self.get_src_dir(), self.get_test_dir()]

    def _get_test_report_name(self, report_extension: str) -> str:
        """Enforces a consistent python report naming convention.

        Args:
            report_extension (str): The end of the requested report's filename including
                the extension.

        Returns:
            str: The name of a pytest report in a standardized format.
        """
        return "_".join(
            [
                get_project_name(project_root=self.project_root),
                get_project_version(project_root=self.project_root),
                self.get_subproject_name(),
                report_extension,
            ],
        )

    def get_bandit_report_name(self) -> str:
        """Get the name of the bandit security report for this project.

        Returns:
            str: The name of a bandit report in a standardized format.
        """
        return self._get_test_report_name(report_extension="bandit_report.txt")

    def get_bandit_report_path(self) -> Path:
        """Get the path of the infra bandit security report for this project.

        Returns:
            Path: Path to the bandit report for this subproject.
        """
        return self.get_reports_dir().joinpath(self.get_bandit_report_name())

    def get_pytest_html_report_name(self) -> str:
        """Get the name of the pytest html report for this subproject.

        Returns:
            str: The name of a pytest html report in a standardized format.
        """
        return self._get_test_report_name(report_extension="pytest_report.html")

    def get_pytest_html_report_path(self) -> Path:
        """Get the path of the pytest html report for this subproject.

        Returns:
            Path: Path to the pytest html report for this subproject.
        """
        return self.get_reports_dir().joinpath(self.get_pytest_html_report_name())

    def get_pytest_xml_report_name(self) -> str:
        """Get the name of the pytest xml report for this subproject.

        Returns:
            str: The name of a pytest xml report in a standardized format.
        """
        return self._get_test_report_name(report_extension="pytest_report.xml")

    def get_pytest_xml_report_path(self) -> Path:
        """Get the path of the pytest xml report for this subproject.

        Returns:
            Path: Path to the pytest xml report for this subproject.
        """
        return self.get_reports_dir().joinpath(self.get_pytest_xml_report_name())

    def get_pytest_xml_coverage_report_name(self) -> str:
        """Get the name of the pytest xml coverage report for this subproject.

        Returns:
            str: The name of a pytest xml coverage report in a standardized format.
        """
        return self._get_test_report_name(report_extension="pytest_coverage_report.xml")

    def get_pytest_xml_coverage_report_path(self) -> Path:
        """Get the path of the pytest xml coverage report for this subproject.

        Returns:
            Path: Path to the pytest xml coverage report for this subproject.
        """
        return self.get_reports_dir().joinpath(
            self.get_pytest_xml_coverage_report_name()
        )

    def get_pytest_html_coverage_report_name(self) -> str:
        """Get the name of the pytest html coverage report for this subproject.

        Returns:
            str: The name of a pytest html coverage report in a standardized format.
        """
        return self._get_test_report_name(report_extension="pytest_coverage_report")

    def get_pytest_html_coverage_report_path(self) -> Path:
        """Get the path of the pytest html coverage report for this subproject.

        Returns:
            Path: Path to the pytest html coverage report for this subproject.
        """
        return self.get_reports_dir().joinpath(
            self.get_pytest_html_coverage_report_name()
        )

    def get_pytest_report_args(self) -> list[str]:
        """Get the args used by pytest for this subproject.

        Returns:
            list[str]: A list of arguments that will be used with pytest for this
                subproject.
        """
        return concatenate_args(
            args=[
                "--cov-report",
                "term-missing",
                "--cov-report",
                f"xml:{self.get_pytest_xml_coverage_report_path()}",
                "--cov-report",
                f"html:{self.get_pytest_html_coverage_report_path()}",
                f"--cov={self.get_root_dir()}",
                f"--junitxml={self.get_pytest_xml_report_path()}",
                f"--html={self.get_pytest_html_report_path()}",
                "--self-contained-html",
            ],
        )


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
