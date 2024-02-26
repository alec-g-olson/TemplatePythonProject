from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    SubprojectContext,
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
from build_support.ci_cd_vars.python_vars import (
    get_bandit_report_name,
    get_bandit_report_path,
    get_coverage_root,
    get_pytest_html_coverage_report_name,
    get_pytest_html_coverage_report_path,
    get_pytest_html_report_name,
    get_pytest_html_report_path,
    get_pytest_report_args,
    get_pytest_xml_coverage_report_name,
    get_pytest_xml_coverage_report_path,
    get_pytest_xml_report_name,
    get_pytest_xml_report_path,
    get_test_report_name,
)
from build_support.dag_engine import concatenate_args

pytest_contexts = list(SubprojectContext)


@pytest.fixture(params=pytest_contexts)
def pytest_context(request: SubRequest) -> SubprojectContext:
    return request.param


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
@pytest.mark.parametrize("report_extension", ["some_extension.ext", "nice_text.txt"])
def test_get_pytest_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
    report_extension: str,
) -> None:
    assert get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension=report_extension,
    ) == "_".join(
        [
            get_project_name(project_root=mock_project_root),
            get_project_version(project_root=mock_project_root),
            pytest_context.value,
            report_extension,
        ],
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_bandit_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="bandit_report.txt",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_path(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_bandit_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_reports_dir(project_root=mock_project_root).joinpath(
        get_bandit_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        ),
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_html_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_report.html",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_report_path(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_html_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_reports_dir(project_root=mock_project_root).joinpath(
        get_pytest_html_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        ),
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_xml_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_report.xml",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_report_path(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_xml_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_reports_dir(project_root=mock_project_root).joinpath(
        get_pytest_xml_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        ),
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_coverage_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_xml_coverage_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_coverage_report.xml",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_coverage_report_path(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_xml_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_reports_dir(project_root=mock_project_root).joinpath(
        get_pytest_xml_coverage_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        ),
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_coverage_report_name(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_html_coverage_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_test_report_name(
        project_root=mock_project_root,
        test_context=pytest_context,
        report_extension="pytest_coverage_report",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_coverage_report_path(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    assert get_pytest_html_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    ) == get_build_reports_dir(project_root=mock_project_root).joinpath(
        get_pytest_html_coverage_report_name(
            project_root=mock_project_root,
            test_context=pytest_context,
        ),
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_coverage_root(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    observed_coverage_root_dir = get_coverage_root(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    if pytest_context == SubprojectContext.BUILD_SUPPORT:
        assert observed_coverage_root_dir == get_build_support_dir(
            project_root=mock_project_root,
        )
    elif pytest_context == SubprojectContext.PYPI:
        assert observed_coverage_root_dir == get_pypi_dir(
            project_root=mock_project_root,
        )
    elif pytest_context == SubprojectContext.DOCUMENTATION_ENFORCEMENT:
        assert observed_coverage_root_dir == get_documentation_enforcement_dir(
            project_root=mock_project_root,
        )
    elif pytest_context == SubprojectContext.PULUMI:
        assert observed_coverage_root_dir == get_pulumi_dir(
            project_root=mock_project_root,
        )
    else:  # assume pulumi if not add the new case
        assert observed_coverage_root_dir == mock_project_root


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_report_args(
    mock_project_root: Path,
    pytest_context: SubprojectContext,
) -> None:
    coverage_xml = get_pytest_xml_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    coverage_html = get_pytest_html_coverage_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    test_xml = get_pytest_xml_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    test_html = get_pytest_html_report_path(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    coverage_root_dir = get_coverage_root(
        project_root=mock_project_root,
        test_context=pytest_context,
    )
    assert get_pytest_report_args(
        project_root=mock_project_root,
        test_context=pytest_context,
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
        ],
    )
