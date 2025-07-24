from datetime import timedelta
from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_runtime_report_path,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)
from build_support.dag_engine import BuildRunReport


@pytest.mark.usefixtures("mock_lightweight_project")
def test_feature_tests_execute_faster_when_cached(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    subproject = get_python_subproject(
        subproject_context=SubprojectContext.PYPI, project_root=mock_project_root
    )
    feature_test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
    )
    feature_test_file = feature_test_dir.joinpath("test_empty_test.py")
    feature_test_file.write_text(
        "from time import sleep\n"
        "\n"
        "def test_something() -> None:\n"
        "    sleep(1)\n"
        "    assert True\n"
    )
    cmd = Popen(
        args=(*make_command_prefix, "test_pypi_features"), cwd=mock_project_root
    )
    cmd.communicate()
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    first_runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    cmd = Popen(
        args=(*make_command_prefix, "test_pypi_features"), cwd=mock_project_root
    )
    cmd.communicate()
    second_runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    first_run_duration = next(
        task.duration
        for task in first_runtime_report.report
        if task.task_name == "SubprojectFeatureTests-PYPI"
    )
    second_run_duration = next(
        task.duration
        for task in second_runtime_report.report
        if task.task_name == "SubprojectFeatureTests-PYPI"
    )
    assert first_run_duration > timedelta(seconds=0.9)
    assert second_run_duration < timedelta(seconds=0.1)
