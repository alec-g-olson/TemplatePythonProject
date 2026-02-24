"""Feature tests for configurable build logging (LOG_LEVEL).

Three levels: INFO = steps only; DEBUG = steps + commands; TRACE = steps + commands
+ task stdout/stderr. Failures always log command, code, stdout, and stderr at ERROR.
"""

import pytest
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


@pytest.mark.usefixtures("mock_lightweight_project")
def test_default_log_level_shows_only_workflow(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """At default (INFO) level only workflow messages appear; no task output."""
    return_code, stdout, stderr = run_command_and_save_logs(
        context=default_command_context, command_args=["format"]
    )
    combined = stdout + stderr
    assert return_code == 0
    assert "Will execute the following tasks:" in combined
    assert "Starting:" in combined
    assert "report:" in combined
    assert "reformatted" not in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_trace_log_level_shows_task_output(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """At LOG_LEVEL=TRACE, task stdout/stderr (e.g. formatter output) is present."""
    return_code, stdout, stderr = run_command_and_save_logs(
        context=default_command_context, command_args=["LOG_LEVEL=TRACE", "format"]
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
    default_command_context: FeatureTestCommandContext,
) -> None:
    """At LOG_LEVEL=DEBUG, command lines are logged (inner docker run)."""
    return_code, stdout, stderr = run_command_and_save_logs(
        context=default_command_context, command_args=["LOG_LEVEL=DEBUG", "format"]
    )
    combined = stdout + stderr
    assert return_code == 0
    assert "docker run" in combined
    assert "ruff" in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_failure_visible_at_default_log_level(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """On task failure, the failure and failing command are visible at default level."""
    get_python_subproject(
        project_root=default_command_context.mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    ).get_test_dir().joinpath("test_type_error_for_logging_test.py").write_text(
        """def some_function() -> None:
    \"\"\"func docstring\"\"\"
    x: int = "not an int"
"""
    )
    default_command_context.expect_failure = True
    return_code, stdout, stderr = run_command_and_save_logs(
        context=default_command_context, command_args=["type_check_build_support"]
    )
    combined = stdout + stderr
    assert return_code != 0
    assert "Failed with code:" in combined
