from pathlib import Path

import pytest

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.project_structure import get_build_dir
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_all_python_subprojects_with_src,
    get_all_python_subprojects_with_test,
    get_python_subproject,
    get_sorted_subproject_contexts,
)


def test_get_subproject_name(
    mock_subproject: PythonSubproject, subproject_context: SubprojectContext
) -> None:
    assert mock_subproject.get_subproject_name() == subproject_context.value


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_build_dir(
    mock_subproject: PythonSubproject, mock_project_root: Path
) -> None:
    expected_build_dir = get_build_dir(project_root=mock_project_root).joinpath(
        mock_subproject.get_subproject_name()
    )
    assert not expected_build_dir.exists()
    assert mock_subproject.get_build_dir() == expected_build_dir
    assert expected_build_dir.exists()


def test_get_reports_dir(mock_subproject: PythonSubproject) -> None:
    expected_reports_dir = mock_subproject.get_build_dir().joinpath("reports")
    assert not expected_reports_dir.exists()
    assert mock_subproject.get_reports_dir() == expected_reports_dir
    assert expected_reports_dir.exists()


def test_get_root_dir(
    mock_subproject: PythonSubproject, mock_project_root: Path
) -> None:
    assert mock_subproject.get_root_dir() == mock_project_root.joinpath(
        mock_subproject.get_subproject_name()
    )


def test_get_src_dir(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_src_dir() == mock_subproject.get_root_dir().joinpath(
        "src"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_python_package_dir(
    mock_subproject: PythonSubproject,
    subproject_context: SubprojectContext,
    mock_project_root: Path,
) -> None:
    if subproject_context == SubprojectContext.PYPI:
        assert (
            mock_subproject.get_python_package_dir()
            == mock_subproject.get_src_dir().joinpath(
                get_project_name(project_root=mock_project_root)
            )
        )
    else:
        assert (
            mock_subproject.get_python_package_dir()
            == mock_subproject.get_src_dir().joinpath(subproject_context.value)
        )


def test_get_test_dir(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_test_dir() == mock_subproject.get_root_dir().joinpath(
        "test"
    )


def test_get_unit_test_dir(mock_subproject: PythonSubproject) -> None:
    assert (
        mock_subproject.get_unit_test_dir()
        == mock_subproject.get_test_dir().joinpath("unit_tests")
    )


def test_get_integration_test_dir(mock_subproject: PythonSubproject) -> None:
    assert (
        mock_subproject.get_integration_test_dir()
        == mock_subproject.get_test_dir().joinpath("integration_tests")
    )


def test_get_src_and_test_dir(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_src_and_test_dir() == [
        mock_subproject.get_src_dir(),
        mock_subproject.get_test_dir(),
    ]


def get_expected_report_name(
    subproject: PythonSubproject, report_extension: str
) -> str:
    return "_".join(
        [
            get_project_name(project_root=subproject.project_root),
            get_project_version(project_root=subproject.project_root),
            subproject.get_subproject_name(),
            report_extension,
        ],
    )


def get_expected_report_path(
    subproject: PythonSubproject, report_extension: str
) -> Path:
    return subproject.get_reports_dir().joinpath(
        get_expected_report_name(
            subproject=subproject, report_extension=report_extension
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_name(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_bandit_report_name() == get_expected_report_name(
        subproject=mock_subproject, report_extension="bandit_report.txt"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_path(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_bandit_report_path() == get_expected_report_path(
        subproject=mock_subproject, report_extension="bandit_report.txt"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_report_name(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_pytest_html_report_name() == get_expected_report_name(
        subproject=mock_subproject, report_extension="pytest_report.html"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_report_path(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_pytest_html_report_path() == get_expected_report_path(
        subproject=mock_subproject, report_extension="pytest_report.html"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_report_name(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_pytest_xml_report_name() == get_expected_report_name(
        subproject=mock_subproject, report_extension="pytest_report.xml"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_report_path(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_pytest_xml_report_path() == get_expected_report_path(
        subproject=mock_subproject, report_extension="pytest_report.xml"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_coverage_report_name(mock_subproject: PythonSubproject) -> None:
    assert (
        mock_subproject.get_pytest_xml_coverage_report_name()
        == get_expected_report_name(
            subproject=mock_subproject, report_extension="pytest_coverage_report.xml"
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_xml_coverage_report_path(mock_subproject: PythonSubproject) -> None:
    assert (
        mock_subproject.get_pytest_xml_coverage_report_path()
        == get_expected_report_path(
            subproject=mock_subproject, report_extension="pytest_coverage_report.xml"
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_coverage_report_name(
    mock_subproject: PythonSubproject,
) -> None:
    assert (
        mock_subproject.get_pytest_html_coverage_report_name()
        == get_expected_report_name(
            subproject=mock_subproject, report_extension="pytest_coverage_report"
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_html_coverage_report_path(
    mock_subproject: PythonSubproject,
) -> None:
    assert (
        mock_subproject.get_pytest_html_coverage_report_path()
        == get_expected_report_path(
            subproject=mock_subproject, report_extension="pytest_coverage_report"
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_report_args(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_pytest_report_args() == [
        "--cov-report",
        "term-missing",
        "--cov-report",
        f"xml:{mock_subproject.get_pytest_xml_coverage_report_path()}",
        "--cov-report",
        f"html:{mock_subproject.get_pytest_html_coverage_report_path()}",
        f"--cov={mock_subproject.get_root_dir()}",
        f"--junitxml={mock_subproject.get_pytest_xml_report_path()}",
        f"--html={mock_subproject.get_pytest_html_report_path()}",
        "--self-contained-html",
    ]


def test_get_python_subproject(mock_project_root: Path) -> None:
    for context in get_sorted_subproject_contexts():
        assert get_python_subproject(
            subproject_context=context, project_root=mock_project_root
        ) == PythonSubproject(
            project_root=mock_project_root, subproject_context=context
        )


def test_get_all_python_subprojects_dict(mock_project_root: Path) -> None:
    assert get_all_python_subprojects_dict(project_root=mock_project_root) == {
        subproject_context: PythonSubproject(
            project_root=mock_project_root, subproject_context=subproject_context
        )
        for subproject_context in SubprojectContext
    }


def test_get_all_python_subprojects_with_src(mock_project_root: Path) -> None:
    context_to_add_src_for = [SubprojectContext.PYPI, SubprojectContext.BUILD_SUPPORT]
    subproject_dict = get_all_python_subprojects_dict(project_root=mock_project_root)
    for subproject_context in context_to_add_src_for:
        src_dir = subproject_dict[subproject_context].get_src_dir()
        src_dir.mkdir(parents=True, exist_ok=True)
    sorted_contexts = sorted(context_to_add_src_for, key=lambda x: x.name)
    expected_subprojects_with_src = [
        get_python_subproject(
            project_root=mock_project_root, subproject_context=context
        )
        for context in sorted_contexts
    ]
    assert (
        get_all_python_subprojects_with_src(project_root=mock_project_root)
        == expected_subprojects_with_src
    )


def test_get_all_python_subprojects_with_test(mock_project_root: Path) -> None:
    context_to_add_test_for = [
        SubprojectContext.PYPI,
        SubprojectContext.DOCUMENTATION_ENFORCEMENT,
    ]
    subproject_dict = get_all_python_subprojects_dict(project_root=mock_project_root)
    for subproject_context in context_to_add_test_for:
        test_dir = subproject_dict[subproject_context].get_test_dir()
        test_dir.mkdir(parents=True, exist_ok=True)
    sorted_contexts = sorted(context_to_add_test_for, key=lambda x: x.name)
    expected_subprojects_with_test = [
        get_python_subproject(
            project_root=mock_project_root, subproject_context=context
        )
        for context in sorted_contexts
    ]
    assert (
        get_all_python_subprojects_with_test(project_root=mock_project_root)
        == expected_subprojects_with_test
    )
