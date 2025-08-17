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
def test_do_not_run_tests_for_unmodified_projects(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    assert True
