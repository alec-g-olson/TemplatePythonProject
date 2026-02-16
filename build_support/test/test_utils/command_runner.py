"""Utility for running commands and saving logs during tests."""

from pathlib import Path
from subprocess import PIPE, Popen

from build_support.ci_cd_vars.project_structure import get_feature_test_log_name


def run_command_and_save_logs(
    args: list[str], cwd: Path, test_name: str, real_project_root_dir: Path
) -> tuple[int, str, str]:
    """Runs a command and saves stdout/stderr to a log file in test_scratch_folder.

    Args:
        args (list[str]): Command arguments to run.
        cwd (Path): Working directory for the command.
        test_name (str): Name of the test (used for log file naming).
        real_project_root_dir (Path): Real project root directory.

    Returns:
        tuple[int, str, str]: Return code, stdout, and stderr.
    """
    log_file = get_feature_test_log_name(
        project_root=real_project_root_dir, test_name=test_name
    )

    cmd = Popen(args=args, cwd=cwd, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = cmd.communicate()
    return_code = cmd.returncode

    # Write logs to file
    with log_file.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Test: {test_name}\n")
        f.write(f"Command: {' '.join(args)}\n")
        f.write(f"Working Directory: {cwd}\n")
        f.write(f"Return Code: {return_code}\n")
        f.write("=" * 80 + "\n\n")
        f.write("STDOUT:\n")
        f.write("-" * 80 + "\n")
        f.write(stdout)
        f.write("\n\n")
        f.write("STDERR:\n")
        f.write("-" * 80 + "\n")
        f.write(stderr)
        f.write("\n")

    return return_code, stdout, stderr
