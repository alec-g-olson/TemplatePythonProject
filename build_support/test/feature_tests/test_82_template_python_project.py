from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path
from build_support.dag_engine import BuildRunReport


@pytest.mark.usefixtures("mock_lightweight_project")
def test_pass_generate_runtime_report_after_dag_execution(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    expected_report_yaml = get_build_runtime_report_path(project_root=mock_project_root)
    assert not expected_report_yaml.exists()
    cmd = Popen(args=(*make_command_prefix, "format"), cwd=mock_project_root)
    cmd.communicate()
    assert cmd.returncode == 0
    parsed_report = BuildRunReport.from_yaml(expected_report_yaml.read_text())
    assert len(parsed_report.report) > 0
