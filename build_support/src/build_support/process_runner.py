"""Module for running processes."""

import itertools
import sys
from enum import Enum

# The purpose of this module is to make subprocess calls
from subprocess import PIPE, Popen  # nosec: B404
from typing import IO, Any, AnyStr


class ProcessVerbosity(Enum):
    """Enum for process verbosity to avoid boolean trap."""

    SILENT = 1
    ALL = 2


def run_piped_processes(
    processes: list[list[Any]], verbosity: ProcessVerbosity = ProcessVerbosity.ALL
) -> None:
    """Runs piped processes as they would be on the command line.

    Args:
        processes (list[list[Any]]): The list of process arguments that will be run
            sequentially.
        verbosity (ProcessVerbosity): Should the process be run silently.

    Returns:
        None
    """
    args_list = [get_str_args(args=args) for args in processes]
    process_strs = [" ".join(args) for args in args_list]
    command_as_str = " | ".join(process_strs)
    if verbosity != ProcessVerbosity.SILENT:
        print(command_as_str, flush=True)  # noqa: T201
    p1 = build_popen(args=args_list[0])
    popen_processes = [p1]
    for args in args_list[1:]:
        last_process = popen_processes[-1]
        next_process = build_popen(args=args, stdin=last_process.stdout)
        popen_processes.append(next_process)
    output, error = popen_processes[-1].communicate()
    return_code = popen_processes[-1].returncode
    resolve_process_results(
        command_as_str=command_as_str,
        output=output,
        error=error,
        return_code=return_code,
        verbosity=verbosity,
    )


def get_output_of_process(
    args: list[Any], verbosity: ProcessVerbosity = ProcessVerbosity.ALL
) -> str:
    """Runs a process and gets the output.

    Args:
        args (list[Any]): A list of arguments that could be run on the command line.
        verbosity (ProcessVerbosity): Should the process be run silently.

    Returns:
        str: The stdout from the subprocess that was run.
    """
    output = run_process(args=args, verbosity=verbosity)
    return output.decode("utf-8").strip()


def run_process(
    args: list[Any], verbosity: ProcessVerbosity = ProcessVerbosity.ALL
) -> bytes:
    """Runs a process.

    Args:
        args (list[Any]): A list of arguments that could be run on the command line.
        verbosity (ProcessVerbosity): Should the process be run silently.

    Returns:
        bytes: The stdout from the subprocess that was run.
    """
    str_args = get_str_args(args=args)
    command_as_str = " ".join(str_args)
    if verbosity != ProcessVerbosity.SILENT:
        print(command_as_str, flush=True)  # noqa: T201
    p = build_popen(args=str_args)
    output, error = p.communicate()
    return_code = p.returncode
    resolve_process_results(
        command_as_str=command_as_str,
        output=output,
        error=error,
        return_code=return_code,
        verbosity=verbosity,
    )
    return output


def build_popen(args: list[str], stdin: IO[AnyStr] | int | None = None) -> Popen[bytes]:
    """Creates a Popes instance based on the arguments.

    Args:
        args (list[str]): The args to pass to the new process.
        stdin (IO | int | None): The stdin to use with the new process.

    Returns:
        Popen: A Popen instance with parameters set by the inputs to this function.
    """
    # As this is currently setup, commands are never injected by external users
    return Popen(  # nosec: B603
        args=args, stdin=stdin, stdout=PIPE, stderr=PIPE
    )


def resolve_process_results(
    command_as_str: str,
    output: bytes,
    error: bytes,
    return_code: int,
    verbosity: ProcessVerbosity = ProcessVerbosity.ALL,
) -> None:
    """Prints outputs and errors and exits as appropriate when a command exits.

    Args:
        command_as_str (str): The command run as it would appear on the command line.
        output (bytes): The stdout from the subprocess that was run.
        error (bytes): The stderr from the subprocess that was run.
        return_code (int): The return code from the subprocess that was run.
        verbosity (ProcessVerbosity): Was the subprocess intended to run silently.

    Returns:
        None
    """
    if output and verbosity != ProcessVerbosity.SILENT:
        print(output.decode("utf-8"), flush=True, end="")  # noqa: T201
    if error:
        print(error.decode("utf-8"), flush=True, end="", file=sys.stderr)  # noqa: T201
    if return_code != 0:
        if verbosity == ProcessVerbosity.SILENT:
            print(  # noqa: T201
                f"{command_as_str}\nFailed with code: {return_code}",
                flush=True,
                file=sys.stderr,
            )
        sys.exit(return_code)


def concatenate_args(args: list[Any | list[Any]]) -> list[str]:
    """Flattens elements and lists of elements into a single list.

    Example:
        >>> concatenate_args([1, 2.5, "str", [2, 3], [42, "1337"]])
        ["1", "2.5", "str", "2", "3", "42", "1337"]

    Args:
        args (list[Any | list[Any]]): List of arguments and lists to flatten.

    Returns:
        list[str]: List of arguments converted to strings.
    """
    all_args_as_lists = [arg if isinstance(arg, list) else [arg] for arg in args]
    return get_str_args(list(itertools.chain.from_iterable(all_args_as_lists)))


def get_str_args(args: list[Any]) -> list[str]:
    """Converts a list of any arguments into strings.

    Args:
        args (list[Any]): Arguments to convert to strings.

    Returns:
        list[str]: List of arguments converted to strings.
    """
    return [str(x) for x in args]
