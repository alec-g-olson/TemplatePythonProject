"""Utility for running commands and saving logs during tests."""

import logging
from pathlib import Path
from subprocess import PIPE, Popen

from build_support.ci_cd_vars.project_structure import get_feature_test_log_name

logger = logging.getLogger(__name__)


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
