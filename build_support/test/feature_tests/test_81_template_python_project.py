from datetime import timedelta

import pytest
from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport
from test_utils.command_runner import FeatureTestCommandContext, run_command


@pytest.mark.usefixtures("mock_lightweight_project_with_single_feature_test")
def test_feature_tests_execute_faster_when_cached(
    command_context: FeatureTestCommandContext,
) -> None:
    return_code, _, _ = run_command(
        command_context,
        ["test_pypi_features"],
        test_name_override=f"{command_context.test_name}_first",
    )
    assert return_code == 0
    expected_report_yaml = get_build_runtime_report_path(
        project_root=command_context.mock_project_root
    )
    first_runtime_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    return_code, _, _ = run_command(
        command_context,
        ["test_pypi_features"],
        test_name_override=f"{command_context.test_name}_second",
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
