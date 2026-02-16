from datetime import timedelta
from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport


@pytest.mark.usefixtures("mock_lightweight_project_with_single_feature_test")
def test_feature_tests_execute_faster_when_cached(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
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
    assert second_run_duration < timedelta(seconds=0.2)
