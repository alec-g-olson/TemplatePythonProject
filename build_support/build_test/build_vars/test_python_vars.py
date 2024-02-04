from pathlib import Path

import pytest
from build_vars.file_and_dir_path_vars import (
    ProjectContext,
    get_build_dir,
    get_build_support_dir,
    get_pulumi_dir,
    get_pypi_dir,
)
from build_vars.project_setting_vars import get_project_name, get_project_version
from build_vars.python_vars import (
    get_bandit_report_name,
    get_bandit_report_path,
    get_coverage_root,
    get_pytest_html_coverage_report_name,
    get_pytest_html_coverage_report_path,
    get_pytest_html_report_name,
    get_pytest_html_report_path,
    get_pytest_report_name,
    get_pytest_xml_coverage_report_name,
    get_pytest_xml_coverage_report_path,
    get_pytest_xml_report_name,
    get_pytest_xml_report_path,
    get_test_report_args,
)
from dag_engine import concatenate_args

pytest_contexts = [target for target in ProjectContext]


@pytest.fixture(params=pytest_contexts)
def pytest_context(request) -> ProjectContext:
    return request.param


@pytest.mark.parametrize("report_extension", ["some_extension.ext", "nice_text.txt"])
def test_get_pytest_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
    report_extension: str,
):
    assert get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension=report_extension,
    ) == "_".join(
        [
            get_project_name(project_root=mock_project_root),
            get_project_version(project_root=mock_project_root),
            pytest_context.value,
            report_extension,
        ]
    )


def test_get_bandit_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_bandit_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="bandit_report.txt",
    )


def test_get_bandit_report_path(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_bandit_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_dir(project_root=mock_project_root).joinpath(
        get_bandit_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        )
    )


def test_get_pytest_html_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_html_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_report.html",
    )


def test_get_pytest_html_report_path(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_html_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_dir(project_root=mock_project_root).joinpath(
        get_pytest_html_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        )
    )


def test_get_pytest_xml_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_xml_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_report.xml",
    )


def test_get_pytest_xml_report_path(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_xml_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_dir(project_root=mock_project_root).joinpath(
        get_pytest_xml_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        )
    )


def test_get_pytest_xml_coverage_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_xml_coverage_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_coverage_report.xml",
    )


def test_get_pytest_xml_coverage_report_path(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_xml_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_dir(project_root=mock_project_root).joinpath(
        get_pytest_xml_coverage_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        )
    )


def test_get_pytest_html_coverage_report_name(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_html_coverage_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_pytest_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_coverage_report",
    )


def test_get_pytest_html_coverage_report_path(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    assert get_pytest_html_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_dir(project_root=mock_project_root).joinpath(
        get_pytest_html_coverage_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        )
    )


def test_get_coverage_root(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    observed_coverage_root_dir = get_coverage_root(
        project_root=mock_project_root, test_context=pytest_context
    )
    if pytest_context == ProjectContext.BUILD_SUPPORT:
        assert observed_coverage_root_dir == get_build_support_dir(
            project_root=mock_project_root
        )
    elif pytest_context == ProjectContext.PYPI:
        assert observed_coverage_root_dir == get_pypi_dir(
            project_root=mock_project_root
        )
    elif pytest_context == ProjectContext.PULUMI:
        assert observed_coverage_root_dir == get_pulumi_dir(
            project_root=mock_project_root
        )
    else:  # assume pulumi if not add the new case
        assert observed_coverage_root_dir == mock_project_root


def test_get_test_report_args(
    mock_project_root: Path,
    mock_local_pyproject_toml_file,
    pytest_context: ProjectContext,
):
    coverage_xml = get_pytest_xml_coverage_report_path(
        project_root=mock_project_root, test_context=pytest_context
    )
    coverage_html = get_pytest_html_coverage_report_path(
        project_root=mock_project_root, test_context=pytest_context
    )
    test_xml = get_pytest_xml_report_path(
        project_root=mock_project_root, test_context=pytest_context
    )
    test_html = get_pytest_html_report_path(
        project_root=mock_project_root, test_context=pytest_context
    )
    coverage_root_dir = get_coverage_root(
        project_root=mock_project_root, test_context=pytest_context
    )
    assert get_test_report_args(
        project_root=mock_project_root, test_context=pytest_context
    ) == concatenate_args(
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
