"""Collection of all functions and variable that are useful in the context of python."""

from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.subproject_structure import PythonSubProject
from build_support.process_runner import concatenate_args


def get_test_report_name(
    project_root: Path,
    subproject: PythonSubProject,
    report_extension: str,
) -> str:
    """Enforces a consistent python report naming convention.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.
        report_extension (str): The end of the requested report's filename including
            the extension.

    Returns:
        str: The name of a pytest report in a standardized format.
    """
    return "_".join(
        [
            get_project_name(project_root=project_root),
            get_project_version(project_root=project_root),
            subproject.subproject_name,
            report_extension,
        ],
    )


def get_bandit_report_name(project_root: Path, subproject: PythonSubProject) -> str:
    """Get the name of the pypi bandit security report.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        str: The name of a bandit report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        subproject=subproject,
        report_extension="bandit_report.txt",
    )


def get_bandit_report_path(project_root: Path, subproject: PythonSubProject) -> Path:
    """Get the path of the pulumi bandit security report.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        Path: Path to the bandit report for the requested subproject context.
    """
    return subproject.get_subproject_reports_dir().joinpath(
        get_bandit_report_name(project_root=project_root, subproject=subproject),
    )


def get_pytest_html_report_name(
    project_root: Path,
    subproject: PythonSubProject,
) -> str:
    """Get the name of the pytest html report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        str: The name of a pytest html report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        subproject=subproject,
        report_extension="pytest_report.html",
    )


def get_pytest_html_report_path(
    project_root: Path,
    subproject: PythonSubProject,
) -> Path:
    """Get the path of the pytest html report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        Path: Path to the pytest html report for the requested subproject context.
    """
    return subproject.get_subproject_reports_dir().joinpath(
        get_pytest_html_report_name(
            project_root=project_root,
            subproject=subproject,
        ),
    )


def get_pytest_xml_report_name(
    project_root: Path,
    subproject: PythonSubProject,
) -> str:
    """Get the name of the pytest xml report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        str: The name of a pytest xml report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        subproject=subproject,
        report_extension="pytest_report.xml",
    )


def get_pytest_xml_report_path(
    project_root: Path,
    subproject: PythonSubProject,
) -> Path:
    """Get the path of the pytest xml report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        Path: Path to the pytest xml report for the requested subproject context.
    """
    return subproject.get_subproject_reports_dir().joinpath(
        get_pytest_xml_report_name(
            project_root=project_root,
            subproject=subproject,
        ),
    )


def get_pytest_xml_coverage_report_name(
    project_root: Path,
    subproject: PythonSubProject,
) -> str:
    """Get the name of the pytest xml coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        str: The name of a pytest xml coverage report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        subproject=subproject,
        report_extension="pytest_coverage_report.xml",
    )


def get_pytest_xml_coverage_report_path(
    project_root: Path,
    subproject: PythonSubProject,
) -> Path:
    """Get the path of the pytest xml coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        Path: Path to the pytest xml coverage report for the requested subproject
            context.
    """
    return subproject.get_subproject_reports_dir().joinpath(
        get_pytest_xml_coverage_report_name(
            project_root=project_root,
            subproject=subproject,
        ),
    )


def get_pytest_html_coverage_report_name(
    project_root: Path,
    subproject: PythonSubProject,
) -> str:
    """Get the name of the pytest html coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        str: The name of a pytest html coverage report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        subproject=subproject,
        report_extension="pytest_coverage_report",
    )


def get_pytest_html_coverage_report_path(
    project_root: Path,
    subproject: PythonSubProject,
) -> Path:
    """Get the path of the pytest html coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        Path: Path to the pytest html coverage report for the requested subproject
            context.
    """
    return subproject.get_subproject_reports_dir().joinpath(
        get_pytest_html_coverage_report_name(
            project_root=project_root,
            subproject=subproject,
        ),
    )


def get_pytest_report_args(
    project_root: Path,
    subproject: PythonSubProject,
) -> list[str]:
    """Get the args used by pytest.

    Args:
        project_root (Path): Path to this project's root.
        subproject (PythonSubProject): The subproject to generate a report for.

    Returns:
        list[str]: A list of arguments that will be used with pytest for the subproject
            context.
    """
    coverage_xml = get_pytest_xml_coverage_report_path(
        project_root=project_root,
        subproject=subproject,
    )
    coverage_html = get_pytest_html_coverage_report_path(
        project_root=project_root,
        subproject=subproject,
    )
    test_xml = get_pytest_xml_report_path(
        project_root=project_root,
        subproject=subproject,
    )
    test_html = get_pytest_html_report_path(
        project_root=project_root,
        subproject=subproject,
    )
    coverage_root_dir = subproject.get_subproject_root()
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
        ],
    )
