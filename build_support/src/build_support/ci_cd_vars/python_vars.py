"""Collection of all functions and variable that are useful in the context of python."""

from pathlib import Path

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    ProjectContext,
    get_build_reports_dir,
    get_build_support_dir,
    get_documentation_enforcement_dir,
    get_pulumi_dir,
    get_pypi_dir,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.dag_engine import concatenate_args


def get_pytest_report_name(
    project_root: Path, test_context: ProjectContext, report_extension: str
) -> str:
    """Enforces a consistent python report naming convention."""
    return "_".join(
        [
            get_project_name(project_root=project_root),
            get_project_version(project_root=project_root),
            test_context.value,
            report_extension,
        ]
    )


def get_bandit_report_name(project_root: Path, test_context: ProjectContext) -> str:
    """Get the name of the pypi bandit security report."""
    return get_pytest_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="bandit_report.txt",
    )


def get_bandit_report_path(project_root: Path, test_context: ProjectContext) -> Path:
    """Get the path of the pulumi bandit security report."""
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_bandit_report_name(project_root=project_root, test_context=test_context)
    )


def get_pytest_html_report_name(
    project_root: Path, test_context: ProjectContext
) -> str:
    """Get the name of the pytest html report."""
    return get_pytest_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_report.html",
    )


def get_pytest_html_report_path(
    project_root: Path, test_context: ProjectContext
) -> Path:
    """Get the path of the pytest html report."""
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_html_report_name(
            project_root=project_root, test_context=test_context
        )
    )


def get_pytest_xml_report_name(project_root: Path, test_context: ProjectContext) -> str:
    """Get the name of the pytest xml report."""
    return get_pytest_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_report.xml",
    )


def get_pytest_xml_report_path(
    project_root: Path, test_context: ProjectContext
) -> Path:
    """Get the path of the pytest xml report."""
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_xml_report_name(project_root=project_root, test_context=test_context)
    )


def get_pytest_xml_coverage_report_name(
    project_root: Path, test_context: ProjectContext
) -> str:
    """Get the name of the pytest xml report."""
    return get_pytest_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_coverage_report.xml",
    )


def get_pytest_xml_coverage_report_path(
    project_root: Path, test_context: ProjectContext
) -> Path:
    """Get the path of the pytest xml report."""
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_xml_coverage_report_name(
            project_root=project_root, test_context=test_context
        )
    )


def get_pytest_html_coverage_report_name(
    project_root: Path, test_context: ProjectContext
) -> str:
    """Get the name of the pytest xml report."""
    return get_pytest_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_coverage_report",
    )


def get_pytest_html_coverage_report_path(
    project_root: Path, test_context: ProjectContext
) -> Path:
    """Get the path of the pytest xml report."""
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_html_coverage_report_name(
            project_root=project_root, test_context=test_context
        )
    )


def get_coverage_root(project_root: Path, test_context: ProjectContext) -> Path:
    """Gets the root folder for the coverage report."""
    match test_context:
        case ProjectContext.BUILD_SUPPORT:
            return get_build_support_dir(project_root=project_root)
        case ProjectContext.PYPI:
            return get_pypi_dir(project_root=project_root)
        case ProjectContext.PULUMI:
            return get_pulumi_dir(project_root=project_root)
        case ProjectContext.DOCUMENTATION_ENFORCEMENT:
            return get_documentation_enforcement_dir(project_root=project_root)
        case ProjectContext.ALL:
            return project_root
        case _:  # pragma: no cover - can't hit if all enums are implemented
            raise ValueError(
                f"{repr(test_context)} is not a valid enum of PyTestContext."
            )


def get_test_report_args(project_root: Path, test_context: ProjectContext) -> list[str]:
    """Get the args used by pytest."""
    coverage_xml = get_pytest_xml_coverage_report_path(
        project_root=project_root, test_context=test_context
    )
    coverage_html = get_pytest_html_coverage_report_path(
        project_root=project_root, test_context=test_context
    )
    test_xml = get_pytest_xml_report_path(
        project_root=project_root, test_context=test_context
    )
    test_html = get_pytest_html_report_path(
        project_root=project_root, test_context=test_context
    )
    coverage_root_dir = get_coverage_root(
        project_root=project_root, test_context=test_context
    )
    return concatenate_args(
        args=[
            "--cov-report",
            "term-missing",
            "--cov-report",
            f"xml:{coverage_xml}",
            "--cov-report",
            f"html:{coverage_html}",
            f"--cov={coverage_root_dir}",
            f"--junitxml={test_xml}",
            f"--html={test_html}",
            "--self-contained-html",
        ]
    )
