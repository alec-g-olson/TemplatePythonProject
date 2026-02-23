"""Feature tests for configurable build logging (LOG_LEVEL).

Three levels: INFO = steps only; DEBUG = steps + commands; TRACE = steps + commands
+ task stdout/stderr. Failures always log command, code, stdout, and stderr at ERROR.
"""

from pathlib import Path
from subprocess import PIPE, Popen

import pytest
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)


@pytest.mark.usefixtures("mock_lightweight_project")
def test_default_log_level_shows_only_workflow(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    """At default (INFO) level only workflow messages appear; no task output."""
    cmd = Popen(
        args=[*make_command_prefix, "format"],
        cwd=mock_project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = cmd.communicate()
    combined = stdout + stderr
    assert cmd.returncode == 0
    assert "Will execute the following tasks:" in combined
    assert "Starting:" in combined
    assert "report:" in combined
    # Task output (e.g. ruff "reformatted") is at TRACE only; commands at DEBUG.
    assert "reformatted" not in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_trace_log_level_shows_task_output(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    """At LOG_LEVEL=TRACE, task stdout/stderr (e.g. formatter output) is present."""
    cmd = Popen(
        args=[*make_command_prefix, "LOG_LEVEL=TRACE", "format"],
        cwd=mock_project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = cmd.communicate()
    combined = stdout + stderr
    assert cmd.returncode == 0
    assert "Will execute the following tasks:" in combined
    # At TRACE we log stdout/stderr; ruff may report "reformatted" or similar.
    assert (
        "reformatted" in combined
        or "All checks passed" in combined
        or "ruff" in combined
    )


@pytest.mark.usefixtures("mock_lightweight_project")
def test_debug_log_level_shows_command_lines(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    """At LOG_LEVEL=DEBUG, command lines are logged (inner docker run)."""
    cmd = Popen(
        args=[*make_command_prefix, "LOG_LEVEL=DEBUG", "format"],
        cwd=mock_project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = cmd.communicate()
    combined = stdout + stderr
    assert cmd.returncode == 0
    # At DEBUG we log the command line before each run (e.g. docker run ... ruff).
    assert "docker run" in combined
    assert "ruff" in combined


@pytest.mark.usefixtures("mock_lightweight_project")
def test_failure_visible_at_default_log_level(
    mock_project_root: Path, make_command_prefix: list[str]
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
    cmd = Popen(
        args=(*make_command_prefix, "type_check_build_support"),
        cwd=mock_project_root,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    stdout, stderr = cmd.communicate()
    combined = stdout + stderr
    assert cmd.returncode != 0
    # Failures always log command, return code, stdout, and stderr at ERROR.
    assert "Failed with code:" in combined
