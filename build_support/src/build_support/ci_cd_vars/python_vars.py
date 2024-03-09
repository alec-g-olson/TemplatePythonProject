"""Collection of all functions and variable that are useful in the context of python."""

from pathlib import Path

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    SubprojectContext,
    get_build_reports_dir,
    get_build_support_dir,
    get_process_and_style_enforcement_dir,
    get_pulumi_dir,
    get_pypi_dir,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.dag_engine import concatenate_args


def get_test_report_name(
    project_root: Path,
    test_context: SubprojectContext,
    report_extension: str,
) -> str:
    """Enforces a consistent python report naming convention.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.
        report_extension (str): The end of the requested report's filename including
            the extension.

    Returns:
        str: The name of a pytest report in a standardized format.
    """
    return "_".join(
        [
            get_project_name(project_root=project_root),
            get_project_version(project_root=project_root),
            test_context.value,
            report_extension,
        ],
    )


def get_bandit_report_name(project_root: Path, test_context: SubprojectContext) -> str:
    """Get the name of the pypi bandit security report.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        str: The name of a bandit report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="bandit_report.txt",
    )


def get_bandit_report_path(project_root: Path, test_context: SubprojectContext) -> Path:
    """Get the path of the pulumi bandit security report.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to the bandit report for the requested subproject context.
    """
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_bandit_report_name(project_root=project_root, test_context=test_context),
    )


def get_pytest_html_report_name(
    project_root: Path,
    test_context: SubprojectContext,
) -> str:
    """Get the name of the pytest html report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        str: The name of a pytest html report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_report.html",
    )


def get_pytest_html_report_path(
    project_root: Path,
    test_context: SubprojectContext,
) -> Path:
    """Get the path of the pytest html report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to the pytest html report for the requested subproject context.
    """
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_html_report_name(
            project_root=project_root,
            test_context=test_context,
        ),
    )


def get_pytest_xml_report_name(
    project_root: Path,
    test_context: SubprojectContext,
) -> str:
    """Get the name of the pytest xml report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        str: The name of a pytest xml report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_report.xml",
    )


def get_pytest_xml_report_path(
    project_root: Path,
    test_context: SubprojectContext,
) -> Path:
    """Get the path of the pytest xml report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to the pytest xml report for the requested subproject context.
    """
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_xml_report_name(
            project_root=project_root,
            test_context=test_context,
        ),
    )


def get_pytest_xml_coverage_report_name(
    project_root: Path,
    test_context: SubprojectContext,
) -> str:
    """Get the name of the pytest xml coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        str: The name of a pytest xml coverage report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_coverage_report.xml",
    )


def get_pytest_xml_coverage_report_path(
    project_root: Path,
    test_context: SubprojectContext,
) -> Path:
    """Get the path of the pytest xml coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to the pytest xml coverage report for the requested subproject
            context.
    """
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_xml_coverage_report_name(
            project_root=project_root,
            test_context=test_context,
        ),
    )


def get_pytest_html_coverage_report_name(
    project_root: Path,
    test_context: SubprojectContext,
) -> str:
    """Get the name of the pytest html coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        str: The name of a pytest html coverage report in a standardized format.
    """
    return get_test_report_name(
        project_root=project_root,
        test_context=test_context,
        report_extension="pytest_coverage_report",
    )


def get_pytest_html_coverage_report_path(
    project_root: Path,
    test_context: SubprojectContext,
) -> Path:
    """Get the path of the pytest html coverage report for the requested context.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to the pytest html coverage report for the requested subproject
            context.
    """
    return get_build_reports_dir(project_root=project_root).joinpath(
        get_pytest_html_coverage_report_name(
            project_root=project_root,
            test_context=test_context,
        ),
    )


def get_coverage_root(project_root: Path, test_context: SubprojectContext) -> Path:
    """Gets the directory that will have coverage calculated based on the subproject.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        Path: Path to directory that will have coverage calculated for the subproject
            context.
    """
    match test_context:
        case SubprojectContext.BUILD_SUPPORT:
            return get_build_support_dir(project_root=project_root)
        case SubprojectContext.PYPI:
            return get_pypi_dir(project_root=project_root)
        case SubprojectContext.PULUMI:
            return get_pulumi_dir(project_root=project_root)
        case SubprojectContext.DOCUMENTATION_ENFORCEMENT:
            return get_process_and_style_enforcement_dir(project_root=project_root)
        case SubprojectContext.ALL:
            return project_root
        case _:  # pragma: no cover - can't hit if all enums are implemented
            msg = f"{test_context!r} is not a valid enum of PyTestContext."
            raise ValueError(msg)


def get_pytest_report_args(
    project_root: Path,
    test_context: SubprojectContext,
) -> list[str]:
    """Get the args used by pytest.

    Args:
        project_root (Path): Path to this project's root.
        test_context (SubprojectContext): An enum stating which subproject we are
            getting a report name for.

    Returns:
        list[str]: A list of arguments that will be used with pytest for the subproject
            context.
    """
    coverage_xml = get_pytest_xml_coverage_report_path(
        project_root=project_root,
        test_context=test_context,
    )
    coverage_html = get_pytest_html_coverage_report_path(
        project_root=project_root,
        test_context=test_context,
    )
    test_xml = get_pytest_xml_report_path(
        project_root=project_root,
        test_context=test_context,
    )
    test_html = get_pytest_html_report_path(
        project_root=project_root,
        test_context=test_context,
    )
    coverage_root_dir = get_coverage_root(
        project_root=project_root,
        test_context=test_context,
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
        ],
    )
