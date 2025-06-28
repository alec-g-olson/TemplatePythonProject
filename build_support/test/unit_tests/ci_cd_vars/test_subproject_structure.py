from pathlib import Path
from typing import cast

import pytest
from _pytest.fixtures import SubRequest

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


@pytest.fixture(params=list(PythonSubproject.TestSuite))
def test_suite(request: SubRequest) -> PythonSubproject.TestSuite:
    return cast(PythonSubproject.TestSuite, request.param)


@pytest.fixture(params=list(PythonSubproject.TestScope))
def test_scope(request: SubRequest) -> PythonSubproject.TestScope:
    return cast(PythonSubproject.TestScope, request.param)


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


def test_get_test_suite_dir(
    mock_subproject: PythonSubproject, test_suite: PythonSubproject.TestSuite
) -> None:
    assert mock_subproject.get_test_suite_dir(
        test_suite=test_suite
    ) == mock_subproject.get_test_dir().joinpath(test_suite.value)


def get_expected_report_name(
    subproject: PythonSubproject,
    test_suite: PythonSubproject.TestSuite | None,
    report_extension: str,
) -> str:
    return "_".join(
        x
        for x in (
            get_project_name(project_root=subproject.project_root),
            get_project_version(project_root=subproject.project_root),
            subproject.get_subproject_name(),
            test_suite.value if test_suite else None,
            report_extension,
        )
        if x
    )


def get_expected_report_path(
    subproject: PythonSubproject,
    test_suite: PythonSubproject.TestSuite | None,
    report_extension: str,
) -> Path:
    return subproject.get_reports_dir().joinpath(
        get_expected_report_name(
            subproject=subproject,
            test_suite=test_suite,
            report_extension=report_extension,
        )
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_name(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_bandit_report_name() == get_expected_report_name(
        subproject=mock_subproject,
        test_suite=None,
        report_extension="bandit_report.txt",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_bandit_report_path(mock_subproject: PythonSubproject) -> None:
    assert mock_subproject.get_bandit_report_path() == get_expected_report_path(
        subproject=mock_subproject,
        test_suite=None,
        report_extension="bandit_report.txt",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_report_name(
    mock_subproject: PythonSubproject,
    test_suite: PythonSubproject.TestSuite,
    test_scope: PythonSubproject.TestScope,
) -> None:
    report_name = mock_subproject.get_pytest_report_name(
        test_suite=test_suite, test_scope=test_scope
    )
    if test_scope == PythonSubproject.TestScope.COMPLETE:
        assert report_name == get_expected_report_name(
            subproject=mock_subproject,
            test_suite=test_suite,
            report_extension="pytest_report.xml",
        )
    else:
        assert report_name == get_expected_report_name(
            subproject=mock_subproject,
            test_suite=test_suite,
            report_extension=f"pytest_report_{test_scope.value}.xml",
        )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_report_path(
    mock_subproject: PythonSubproject,
    test_suite: PythonSubproject.TestSuite,
    test_scope: PythonSubproject.TestScope,
) -> None:
    report_path = mock_subproject.get_pytest_report_path(
        test_suite=test_suite, test_scope=test_scope
    )
    if test_scope == PythonSubproject.TestScope.COMPLETE:
        assert report_path == get_expected_report_path(
            subproject=mock_subproject,
            test_suite=test_suite,
            report_extension="pytest_report.xml",
        )
    else:
        assert report_path == get_expected_report_path(
            subproject=mock_subproject,
            test_suite=test_suite,
            report_extension=f"pytest_report_{test_scope.value}.xml",
        )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_coverage_report_name(
    mock_subproject: PythonSubproject, test_suite: PythonSubproject.TestSuite
) -> None:
    assert mock_subproject.get_pytest_coverage_report_name(
        test_suite=test_suite
    ) == get_expected_report_name(
        subproject=mock_subproject,
        test_suite=test_suite,
        report_extension="pytest_coverage_report.xml",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_coverage_report_path(
    mock_subproject: PythonSubproject, test_suite: PythonSubproject.TestSuite
) -> None:
    assert mock_subproject.get_pytest_coverage_report_path(
        test_suite=test_suite
    ) == get_expected_report_path(
        subproject=mock_subproject,
        test_suite=test_suite,
        report_extension="pytest_coverage_report.xml",
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_whole_test_suite_report_args(
    mock_subproject: PythonSubproject,
) -> None:
    for test_suite in (
        test_suite
        for test_suite in PythonSubproject.TestSuite
        if test_suite != PythonSubproject.TestSuite.FEATURE_TESTS
    ):
        test_scope = PythonSubproject.TestScope.COMPLETE
        test_report_path = mock_subproject.get_pytest_report_path(
            test_suite=test_suite, test_scope=test_scope
        )
        coverage_report_path = mock_subproject.get_pytest_coverage_report_path(
            test_suite=test_suite
        )
        if test_suite == PythonSubproject.TestSuite.UNIT_TESTS:
            expected_args = [
                "--cov-report",
                "term-missing",
                f"--cov={mock_subproject.get_test_suite_dir(test_suite=test_suite)}",
                f"--junitxml={test_report_path}",
                f"--cov={mock_subproject.get_src_dir()}",
                f"--cov-report=xml:{coverage_report_path}",
            ]
        else:
            expected_args = [
                "--cov-report",
                "term-missing",
                f"--cov={mock_subproject.get_test_suite_dir(test_suite=test_suite)}",
                f"--junitxml={test_report_path}",
            ]
        assert (
            mock_subproject.get_pytest_whole_test_suite_report_args(
                test_suite=test_suite
            )
            == expected_args
        )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_pytest_feature_test_report_args(mock_subproject: PythonSubproject) -> None:
    report_path = mock_subproject.get_pytest_report_path(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS,
        test_scope=PythonSubproject.TestScope.SINGLE_FILE,
    )
    assert mock_subproject.get_pytest_feature_test_report_args() == [
        f"--junitxml={report_path}"
    ]


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_file_cache_yaml(mock_subproject: PythonSubproject) -> None:
    expected_file_cache_yaml = mock_subproject.get_build_dir().joinpath(
        "file_cache.yaml"
    )
    assert mock_subproject.get_file_cache_yaml() == expected_file_cache_yaml


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
    context_to_add_test_for = [SubprojectContext.PYPI, SubprojectContext.BUILD_SUPPORT]
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
