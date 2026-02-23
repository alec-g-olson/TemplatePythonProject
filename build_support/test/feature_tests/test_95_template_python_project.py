"""Feature tests for configurable build logging (LOG_LEVEL).

Three levels: INFO = steps only; DEBUG = steps + commands; TRACE = steps + commands
+ task stdout/stderr. Failures always log command, code, stdout, and stderr at ERROR.
"""

from pathlib import Path

import pytest
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from test_utils.command_runner import run_command_and_save_logs


@pytest.mark.usefixtures("mock_lightweight_project")
def test_default_log_level_shows_only_workflow(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """At default (INFO) level only workflow messages appear; no task output."""
    return_code, stdout, stderr = run_command_and_save_logs(
        args=[*make_command_prefix, "format"],
        cwd=mock_project_root,
        test_name="test_default_log_level_shows_only_workflow",
        real_project_root_dir=real_project_root_dir,
    )
    combined = stdout + stderr
    assert return_code == 0
    assert "Will execute the following tasks:" in combined
    assert "Starting:" in combined
    assert "report:" in combined
    assert "reformatted" not in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_trace_log_level_shows_task_output(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """At LOG_LEVEL=TRACE, task stdout/stderr (e.g. formatter output) is present."""
    return_code, stdout, stderr = run_command_and_save_logs(
        args=[*make_command_prefix, "LOG_LEVEL=TRACE", "format"],
        cwd=mock_project_root,
        test_name="test_trace_log_level_shows_task_output",
        real_project_root_dir=real_project_root_dir,
    )
    combined = stdout + stderr
    assert return_code == 0
    assert "Will execute the following tasks:" in combined
    assert (
        "reformatted" in combined
        or "All checks passed" in combined
        or "ruff" in combined
    )


@pytest.mark.usefixtures("mock_lightweight_project")
def test_debug_log_level_shows_command_lines(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """At LOG_LEVEL=DEBUG, command lines are logged (inner docker run)."""
    return_code, stdout, stderr = run_command_and_save_logs(
        args=[*make_command_prefix, "LOG_LEVEL=DEBUG", "format"],
        cwd=mock_project_root,
        test_name="test_debug_log_level_shows_command_lines",
        real_project_root_dir=real_project_root_dir,
    )
    combined = stdout + stderr
    assert return_code == 0
    assert "docker run" in combined
    assert "ruff" in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_failure_visible_at_default_log_level(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """On task failure, the failure and failing command are visible at default level."""
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    ).get_test_dir().joinpath("test_type_error_for_logging_test.py").write_text(
        """def some_function(items) -> list:
    \"\"\"func docstring\"\"\"
    return items
"""
    )
    return_code, stdout, stderr = run_command_and_save_logs(
        args=[*make_command_prefix, "type_check_build_support"],
        cwd=mock_project_root,
        test_name="test_failure_visible_at_default_log_level",
        real_project_root_dir=real_project_root_dir,
        expect_failure=True,
    )
    combined = stdout + stderr
    assert return_code != 0
    assert "Failed with code:" in combined
