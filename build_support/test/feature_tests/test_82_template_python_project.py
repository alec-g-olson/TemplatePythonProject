from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest
from test_utils.command_runner import run_command_and_save_logs

from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_pass_generate_runtime_report_after_dag_execution(
    mock_project_root: Path,
    make_command_prefix_without_tag_suffix: list[str],
    real_project_root_dir: Path,
    request: SubRequest,
) -> None:
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    assert not expected_report_yaml.exists()
    return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix_without_tag_suffix, "format"],
        cwd=mock_project_root,
        test_name=request.node.name,
        real_project_root_dir=real_project_root_dir,
    )
    assert return_code == 0
    parsed_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    assert len(parsed_report.report) > 0
