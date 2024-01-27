"""Module for implementing PyPi domain specific tasks."""

from pathlib import Path

from build_tasks.common_build_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    PushTags,
    TestPythonStyle,
)
from common_vars import (
    THREADS_AVAILABLE,
    get_build_dir,
    get_dev_docker_command,
    get_dist_dir,
    get_prod_docker_command,
    get_project_name,
    get_project_version,
    get_pypi_src_and_test,
    get_temp_dist_dir,
)
from dag_engine import TaskNode, concatenate_args, run_process


def get_html_report_name(project_root: Path) -> str:
    """Get the name of the pytest html report."""
    return (
        get_project_name(project_root=project_root)
        + "_test_report_"
        + get_project_version(project_root=project_root)
        + ".html"
    )


def get_html_report_path(project_root: Path) -> Path:
    """Get the name of the pytest html report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_html_report_name(project_root=project_root)
    )


def get_xml_report_name(project_root: Path) -> str:
    """Get the name of the pytest xml report."""
    return (
        get_project_name(project_root=project_root)
        + "_test_report_"
        + get_project_version(project_root=project_root)
        + ".xml"
    )


def get_xml_report_path(project_root: Path) -> Path:
    """Get the name of the pytest xml report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_xml_report_name(project_root=project_root)
    )


def get_xml_coverage_report_name(project_root: Path) -> str:
    """Get the name of the pytest xml report."""
    return (
        get_project_name(project_root=project_root)
        + "_coverage_report_"
        + get_project_version(project_root=project_root)
        + ".xml"
    )


def get_xml_coverage_report_path(project_root: Path) -> Path:
    """Get the name of the pytest xml report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_xml_coverage_report_name(project_root=project_root)
    )


def get_html_coverage_report_name(project_root: Path) -> str:
    """Get the name of the pytest xml report."""
    return (
        get_project_name(project_root=project_root)
        + "_coverage_report_"
        + get_project_version(project_root=project_root)
    )


def get_html_coverage_report_path(project_root: Path) -> Path:
    """Get the name of the pytest xml report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_html_coverage_report_name(project_root=project_root)
    )


def get_test_report_args(project_root: Path) -> list[str]:
    """Get the args used by pytest."""
    return concatenate_args(
        args=[
            "--cov-report",
            "term-missing",
            "--cov-report",
            f"xml:build/{get_xml_coverage_report_path(project_root=project_root)}",
            "--cov-report",
            f"html:build/{get_html_coverage_report_path(project_root=project_root)}",
            "--cov=.",
            f"--junitxml=build/{get_xml_report_path(project_root=project_root)}",
            f"--html=build/{get_html_report_path(project_root=project_root)}",
            "--self-contained-html",
        ]
    )


class TestPypi(TaskNode):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures dev env is built."""
        return [BuildDevEnvironment()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Tests the PyPi package."""
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_test_report_args(project_root=docker_project_root),
                    get_pypi_src_and_test(project_root=docker_project_root),
                ]
            )
        )


class BuildPypi(TaskNode):
    """Task for building PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure all python checks are passing and prod env exists."""
        return [
            TestPypi(),
            TestPythonStyle(),
            BuildProdEnvironment(),
        ]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Builds PyPi package."""
        run_process(
            args=concatenate_args(
                args=[
                    get_prod_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "rm",
                    "-rf",
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_prod_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "poetry",
                    "build",
                ]
            )
        )
        # Todo: clean this up once a new version of poetry supporting "-o" is released
        run_process(
            args=concatenate_args(
                args=[
                    get_prod_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "mv",
                    get_temp_dist_dir(project_root=docker_project_root),
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )


class PushPypi(TaskNode):
    """Pushes the PyPi package.  Will move to combined once a repo is managed in Pulumi."""

    def required_tasks(self) -> list[TaskNode]:
        """Must build PyPi and push git tags before PyPi is pushed."""
        return [PushTags(), BuildPypi()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Push PyPi."""
