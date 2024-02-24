"""Shared logic across all tasks and how to run them in a DAG."""

import itertools
import sys
from abc import ABC, abstractmethod
from functools import cache
from os import environ, setgid, setuid
from pathlib import Path
from pwd import getpwuid

# The purpose of this module is to make subprocess calls
from subprocess import PIPE, Popen  # nosec: B404
from typing import Any, Callable


class TaskNode(ABC):
    """An abstract representation of a task that can be run in a DAG."""

    def task_label(self) -> str:
        """A unique label for each task, used when building the DAG.

        Returns:
            str: The class name of the task.
        """
        return self.__class__.__name__

    def __eq__(self, other: object) -> bool:
        """Checks if this is equal to the other item.

        Args:
            other (object): The other object to compare equality with.

        Returns:
            bool: True if equal, otherwise false.
        """
        return isinstance(other, TaskNode) and self.task_label() == other.task_label()

    def __hash__(self) -> int:
        """Calculates a hash value for use in dictionaries.

        Returns:
            int: The hash value of this task.
        """
        return hash(self.task_label())

    @abstractmethod
    def required_tasks(self) -> list["TaskNode"]:
        """Will return the tasks required to start the current task.

        Returns:
            list[TaskNode]: A list of the tasks that must be completed
                before this one can be run.
        """

    @abstractmethod
    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Will contain the logic of each task.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """


def _add_tasks_to_list_with_dfs(
    execution_order: list[TaskNode],
    tasks_added: set[TaskNode],
    task_to_add: TaskNode,
) -> None:
    if task_to_add not in tasks_added:
        for required_task in task_to_add.required_tasks():
            _add_tasks_to_list_with_dfs(
                execution_order=execution_order,
                tasks_added=tasks_added,
                task_to_add=required_task,
            )
        tasks_added.add(task_to_add)
        execution_order.append(task_to_add)


def get_task_execution_order(requested_tasks: list[TaskNode]) -> list[TaskNode]:
    """Gets the order that tasks should be executed in.

    Args:
        requested_tasks (list[TaskNode]): A list of tasks to execute.

    Returns:
        list[TaskNode]: A list of all tasks needed in order to execute the requested
            tasks in order of execution.  Order of requested_tasks preserved when
            possible.
    """
    execution_order: list[TaskNode] = []
    tasks_added: set[TaskNode] = set()
    for task in requested_tasks:
        _add_tasks_to_list_with_dfs(
            execution_order=execution_order,
            tasks_added=tasks_added,
            task_to_add=task,
        )
    return execution_order


def run_tasks(
    tasks: list[TaskNode],
    non_docker_project_root: Path,
    docker_project_root: Path,
    local_user_uid: int,
    local_user_gid: int,
) -> None:
    """Builds the DAG required for a task and runs the DAG.

    Args:
        tasks (list[TaskNode]): Tasks that will be executed, along with prerequisite
            tasks.
        docker_project_root (Path): Path to this project's root when running
            in docker containers.
        non_docker_project_root (Path): Path to this project's root on the local
            machine.
        local_user_uid (int): The local user's users id, used when tasks need to be
            run by the local user.
        local_user_gid (int): The local user's group id, used when tasks need to be
            run by the local user.

    Returns:
        None
    """
    task_execution_order = get_task_execution_order(requested_tasks=tasks)
    print("Will execute the following tasks:", flush=True)
    for task in task_execution_order:
        print(f"  - {task.task_label()}", flush=True)
    for task in task_execution_order:
        print(f"Starting: {task.task_label()}", flush=True)
        task.run(
            non_docker_project_root=non_docker_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_user_uid,
            local_user_gid=local_user_gid,
        )


def get_str_args(args: list[Any]) -> list[str]:
    """Converts a list of any arguments into strings.

    Args:
        args (list[Any]): Arguments to convert to strings.

    Returns:
        list[str]: List of arguments converted to strings.
    """
    return [str(x) for x in args]


def concatenate_args(args: list[Any | list[Any]]) -> list[str]:
    """Flattens elements and lists of elements into a single list.

    Example:
        >>> concatenate_args([1, 2.5, "str", [2,3], [42, "1337"]])
        ["1", "2.5", "str", "2", "3", "42", "1337"]

    Args:
        args (list[Any | list[Any]]): List of arguments and lists to flatten.

    Returns:
        list[str]: List of arguments converted to strings.
    """
    all_args_as_lists = [arg if isinstance(arg, list) else [arg] for arg in args]
    return get_str_args(list(itertools.chain.from_iterable(all_args_as_lists)))


def resolve_process_results(
    command_as_str: str,
    output: bytes,
    error: bytes,
    return_code: int,
    silent: bool = False,
) -> None:
    """Prints outputs and errors and exits as appropriate when a command exits.

    Args:
        command_as_str (str): The command run as it would appear on the command line.
        output (bytes): The stdout from the subprocess that was run.
        error (bytes): The stderr from the subprocess that was run.
        return_code (int): The return code from the subprocess that was run.
        silent (bool): Was the subprocess intended to run silently.

    Returns:
        None
    """
    if output and not silent:
        print(output.decode("utf-8"), flush=True, end="")
    if error:
        print(error.decode("utf-8"), flush=True, end="", file=sys.stderr)
    if return_code != 0:
        if silent:
            print(
                f"{command_as_str}\nFailed with code: {return_code}",
                flush=True,
                file=sys.stderr,
            )
        exit(return_code)


@cache
def demote_process_to_user(user_uid: int, user_gid: int) -> Callable[[], None]:
    """Creates a function that changes the user.

    Args:
        user_uid (int): The user's OS user ID.
        user_gid (int): The user's OS group ID.

    Returns:
        Callable[[], None]: A function that changes the user to the user specified
            by the provided user ID and group ID.
    """

    def demote_to_specific_user():
        setgid(user_gid)
        setuid(user_uid)
        environ["HOME"] = f"/home/{getpwuid(user_uid)[0]}/"

    return demote_to_specific_user


def run_process(
    args: list[Any], local_user_uid: int = 0, local_user_gid: int = 0, silent=False
) -> bytes:
    """Runs a process.

    Args:
        args (list[Any]): A list of arguments that could be run on the command line.
        local_user_uid (int): The local user's user ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        local_user_gid (int): The local user's group ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        silent (bool): Should the process be run silently.  Defaults to False.

    Returns:
        bytes: The stdout from the subprocess that was run.
    """
    args = get_str_args(args=args)
    command_as_str = " ".join(args)
    if not silent:
        print(command_as_str, flush=True)
    run_as_user_func = None
    if local_user_uid or local_user_gid:
        run_as_user_func = demote_process_to_user(
            user_uid=local_user_uid, user_gid=local_user_gid
        )
    # As this is currently setup, commands are never injected by external users
    p = Popen(
        args,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        bufsize=-1,
        shell=False,
        preexec_fn=run_as_user_func,
    )  # nosec: B603
    output, error = p.communicate()
    return_code = p.returncode
    resolve_process_results(
        command_as_str=command_as_str,
        output=output,
        error=error,
        return_code=return_code,
        silent=silent,
    )
    return output


def get_output_of_process(
    args: list[Any],
    local_user_uid: int = 0,
    local_user_gid: int = 0,
    silent=False,
) -> str:
    """Runs a process and gets the output.

    Args:
        args (list[Any]): A list of arguments that could be run on the command line.
        local_user_uid (int): The local user's user ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        local_user_gid (int): The local user's group ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        silent (bool): Should the process be run silently.  Defaults to False.

    Returns:
        str: The stdout from the subprocess that was run.
    """
    output = run_process(
        args=args,
        local_user_uid=local_user_uid,
        local_user_gid=local_user_gid,
        silent=silent,
    )
    return output.decode("utf-8").strip()


def run_piped_processes(
    processes: list[list[Any]],
    local_user_uid: int = 0,
    local_user_gid: int = 0,
    silent=False,
) -> None:
    """Runs piped processes as they would be on the command line.

    Args:
        processes (list[list[Any]]): The list of process arguments that will be run
            sequentially.
        local_user_uid (int): The local user's user ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        local_user_gid (int): The local user's group ID, used to run the process as
            the local user. Defaults to 0, runs as root.
        silent (bool): Should the process be run silently.  Defaults to False.

    Returns:
        None
    """
    args_list = [get_str_args(args=args) for args in processes]
    process_strs = [" ".join(args) for args in args_list]
    command_as_str = " | ".join(process_strs)
    if not silent:
        print(command_as_str, flush=True)
    run_as_user_func = None
    if local_user_uid or local_user_gid:
        run_as_user_func = demote_process_to_user(
            user_uid=local_user_uid, user_gid=local_user_gid
        )
    # As this is currently setup, commands are never injected by external users
    p1 = Popen(
        args=args_list[0], stdout=PIPE, shell=False, preexec_fn=run_as_user_func
    )  # nosec: B603
    popen_processes = [p1]
    for args in args_list[1:]:
        last_process = popen_processes[-1]
        # As this is currently setup, commands are never injected by external users
        next_process = Popen(  # nosec: B603
            args=args,
            stdin=last_process.stdout,
            stdout=PIPE,
            shell=False,
            preexec_fn=run_as_user_func,
        )
        popen_processes.append(next_process)
    output, error = popen_processes[-1].communicate()
    return_code = popen_processes[-1].returncode
    resolve_process_results(
        command_as_str=command_as_str,
        output=output,
        error=error,
        return_code=return_code,
        silent=silent,
    )
