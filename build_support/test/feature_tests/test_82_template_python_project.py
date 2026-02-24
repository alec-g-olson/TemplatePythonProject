import pytest
from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_pass_generate_runtime_report_after_dag_execution(
    default_command_context: FeatureTestCommandContext,
) -> None:
    expected_report_yaml = get_build_runtime_report_path(
        project_root=default_command_context.mock_project_root
    )
    assert not expected_report_yaml.exists()
    return_code, _, _ = run_command_and_save_logs(default_command_context, ["format"])
    assert return_code == 0
    parsed_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    assert len(parsed_report.report) > 0
