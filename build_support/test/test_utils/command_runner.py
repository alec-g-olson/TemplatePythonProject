"""Utility for running commands and saving logs during tests."""

import logging
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen

from build_support.ci_cd_vars.project_structure import get_feature_test_log_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeatureTestCommandContext:
    """Bundles arguments needed to run a make command and save logs in feature tests."""

    mock_project_root: Path
    make_command_prefix: list[str]
    real_project_root_dir: Path
    test_name: str


def run_command(
    context: FeatureTestCommandContext,
    args_suffix: list[str],
    expect_failure: bool = False,
    test_name_override: str | None = None,
) -> tuple[int, str, str]:
    """Runs a make-style command using context and saves stdout/stderr to a log file.

    Args:
        context: Bundled mock project root, make prefix, real project root, test name.
        args_suffix: Extra arguments appended after context.make_command_prefix
            (e.g. ["type_check_pypi"] or ["check_process"]).
        expect_failure: If True, a non-zero return code will not trigger ERROR logging.
        test_name_override: If set, used for the log file name instead of
        context.test_name.

    Returns:
        tuple[int, str, str]: Return code, stdout, and stderr.
    """
    test_name = (
        test_name_override if test_name_override is not None else context.test_name
    )
    return run_command_and_save_logs(
        args=[*context.make_command_prefix, *args_suffix],
        cwd=context.mock_project_root,
        test_name=test_name,
        real_project_root_dir=context.real_project_root_dir,
        expect_failure=expect_failure,
    )


def run_command_and_save_logs(
    args: list[str],
    cwd: Path,
    test_name: str,
    real_project_root_dir: Path,
    expect_failure: bool = False,
) -> tuple[int, str, str]:
    """Runs a command and saves stdout/stderr to a log file in test_scratch_folder.

    Args:
        args (list[str]): Command arguments to run.
        cwd (Path): Working directory for the command.
        test_name (str): Name of the test (used for log file naming).
        real_project_root_dir (Path): Real project root directory.
        expect_failure (bool): If True, a non-zero return code will not trigger
            logging of the log content at ERROR level. Default False.

    Returns:
        tuple[int, str, str]: Return code, stdout, and stderr.
    """
    log_file = get_feature_test_log_name(
        project_root=real_project_root_dir, test_name=test_name
    )

    cmd = Popen(args=args, cwd=cwd, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = cmd.communicate()
    return_code = cmd.returncode

    line_break_strong = "=" * 80
    line_break_weak = "-" * 80

    log_content = (
        f"{line_break_strong}\n"
        f"Test: {test_name}\n"
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

    if (return_code != 0) and not expect_failure:
        logger.error("%s", log_content)

    return return_code, stdout, stderr
