"""Utility for running commands and saving logs during feature tests.

Feature tests run make (or other commands) via a single entry point:
run_command_and_save_logs(context, command_args). The default context is
provided by the default_command_context fixture in conftest. Tests that need
different behavior copy the context and override the desired fields;
tests that need a different args prefix (e.g. test_107) override
args_prefix on the copy. Output is always saved to a log file.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen

from build_support.ci_cd_vars.project_structure import get_feature_test_log_name

logger = logging.getLogger(__name__)


@dataclass
class FeatureTestCommandContext:
    """Bundles everything needed to run a command and save a log in feature tests.

    The default context is provided by the default_command_context fixture. Tests that
    need different behavior copy the fixture and override individual fields
    (e.g. ``expect_failure``, ``log_name``, or ``args_prefix``).

    Note: This dataclass is intentionally not frozen. We allow mutation so
    tests can copy the default context and override individual fields without
    repeating the rest; overriding is the common case in feature tests.
    """

    args_prefix: list[str]
    mock_project_root: Path
    real_project_root_dir: Path
    test_name: str
    log_name: str
    expect_failure: bool = False



def run_command_and_save_logs(
    context: FeatureTestCommandContext, command_args: list[str]
) -> tuple[int, str, str]:
    """Run a command and save stdout/stderr to a log file.

    Full command is context.args_prefix + command_args, run in
    context.mock_project_root. Log file name is context.log_name (defaults
    to context.test_name). Use the default_command_context fixture for the default
    context; copy and override fields when needed.

    Args:
        context: Bundled args prefix, cwd, project root, test name, and
            options (expect_failure, log_name).
        command_args: Arguments appended to context.args_prefix (e.g.
            ["type_checks"] or ["echo_image_tags"]).

    Returns:
        tuple[int, str, str]: Return code, stdout, and stderr.
    """
    args = [*context.args_prefix, *command_args]
    cwd = context.mock_project_root
    log_name = context.log_name
    log_file = get_feature_test_log_name(
        project_root=context.real_project_root_dir, test_name=log_name
    )

    cmd = Popen(args=args, cwd=cwd, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = cmd.communicate()
    return_code = cmd.returncode

    line_break_strong = "=" * 80
    line_break_weak = "-" * 80

    log_content = (
        f"{line_break_strong}\n"
        f"Test: {log_name}\n"
        f"Command: {' '.join(args)}\n"
        f"Working Directory: {cwd}\n"
        f"Return Code: {return_code}\n"
        f"{line_break_strong}\n\n"
        "STDOUT:\n"
        f"{line_break_weak}\n\n"
        f"{stdout}\n\n"
        "STDERR:\n"
        f"{line_break_weak}\n\n"
        f"{stderr}\n"
    )
    log_file.write_text(log_content, encoding="utf-8")

    if (return_code != 0) and not context.expect_failure:
        logger.error("%s", log_content)

    return return_code, stdout, stderr
