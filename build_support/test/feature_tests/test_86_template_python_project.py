from datetime import timedelta
from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_tasks.validation_tasks import (
    SubprojectFeatureTests,
    SubprojectUnitTests,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_runtime_report_path,
)
from build_support.ci_cd_vars.project_structure import (
    get_dockerfile,
    get_poetry_lock_file,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)
from build_support.dag_engine import BuildRunReport


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_do_not_run_tests_for_unmodified_projects(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    cmd = Popen(args=(*make_command_prefix, "test"), cwd=mock_project_root)
    cmd.communicate()
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())

    assert all(
        task.duration < timedelta(seconds=0.1)
        for task in runtime_report.report
        if task.task_name.startswith(SubprojectFeatureTests.__class__.__name__)
        or task.task_name.startswith(SubprojectUnitTests.__class__.__name__)
    )


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_run_tests_for_single_modified_subproject(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    subproject = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=mock_project_root
    )
    subproject_pkg_dir = subproject.get_python_package_dir()
    subproject_src_file = subproject_pkg_dir.joinpath("src_file.py")
    subproject_src_file.write_text(
        "from time import sleep\n"
        "\n"
        "def add_slow(a: int, b: int) -> int:\n"
        "    sleep(0.5)\n"
        "    return a + b\n"
        "\n"
        "def subtract_slow(a: int, b: int) -> int:\n"
        "    sleep(0.5)\n"
        "    return a - b\n"
    )
    project_unit_test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    project_unit_test_file = project_unit_test_dir.joinpath("test_src_file.py")
    project_unit_test_file.write_text(
        "from src_file import add_slow, subtract_slow\n"
        "\n"
        "def test_add_slow() -> None:\n"
        "    assert add_slow(2, 3) == 5\n"
        "\n"
        "def test_subtract_slow() -> None:\n"
        "    assert subtract_slow(2, 3) == -1\n"
    )
    cmd = Popen(args=(*make_command_prefix, "test"), cwd=mock_project_root)
    cmd.communicate()
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())

    assert all(
        task.duration < timedelta(seconds=0.1)
        for task in runtime_report.report
        if (
            task.task_name.startswith(SubprojectFeatureTests.__class__.__name__)
            or task.task_name.startswith(SubprojectUnitTests.__class__.__name__)
        )
        and not task.task_name.endswith(SubprojectContext.PYPI.name)
    )
    assert all(
        task.duration > timedelta(seconds=0.9)
        for task in runtime_report.report
        if (
            task.task_name.startswith(SubprojectFeatureTests.__class__.__name__)
            or task.task_name.startswith(SubprojectUnitTests.__class__.__name__)
        )
        and task.task_name.endswith(SubprojectContext.PYPI.name)
    )


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_run_all_tests_if_dockerfile_modified(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    dockerfile = get_dockerfile(project_root=mock_project_root)
    dockerfile_contents = dockerfile.read_text()
    dockerfile.write_text(dockerfile_contents + "\n")
    cmd = Popen(args=(*make_command_prefix, "test"), cwd=mock_project_root)
    cmd.communicate()
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())

    assert all(
        task.duration > timedelta(seconds=0.9)
        for task in runtime_report.report
        if task.task_name.startswith(SubprojectFeatureTests.__class__.__name__)
        or task.task_name.startswith(SubprojectUnitTests.__class__.__name__)
    )


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_run_all_tests_if_poetry_lock_modified(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    poetry_lock_file = get_poetry_lock_file(project_root=mock_project_root)
    poetry_lock_file_contents = poetry_lock_file.read_text()
    poetry_lock_file.write_text(poetry_lock_file_contents + "\n")
    cmd = Popen(args=(*make_command_prefix, "test"), cwd=mock_project_root)
    cmd.communicate()
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())

    assert all(
        task.duration > timedelta(seconds=0.9)
        for task in runtime_report.report
        if task.task_name.startswith(SubprojectFeatureTests.__class__.__name__)
        or task.task_name.startswith(SubprojectUnitTests.__class__.__name__)
    )
