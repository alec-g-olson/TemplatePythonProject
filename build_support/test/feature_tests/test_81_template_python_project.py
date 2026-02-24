import copy
from datetime import timedelta

import pytest
from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


@pytest.mark.usefixtures("mock_lightweight_project_with_single_feature_test")
def test_feature_tests_execute_faster_when_cached(
    default_command_context: FeatureTestCommandContext,
) -> None:
    default_command_context.log_name = f"{default_command_context.test_name}_first"
    return_code, _, _ = run_command_and_save_logs(
        context=default_command_context, command_args=["test_pypi_features"]
    )
    assert return_code == 0
    expected_report_yaml = get_build_runtime_report_path(
        project_root=default_command_context.mock_project_root
    )
    first_runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    second_context = copy.copy(default_command_context)
    second_context.log_name = f"{default_command_context.test_name}_second"
    return_code, _, _ = run_command_and_save_logs(
        context=second_context, command_args=["test_pypi_features"]
    )
    assert return_code == 0
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
