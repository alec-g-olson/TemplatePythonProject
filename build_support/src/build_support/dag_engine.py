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
from typing import Any


class TaskNode(ABC):
    """An abstract representation of a task that can be run in a DAG."""

    def task_label(self) -> str:
        """A unique label for each task, used when building the DAG.

        Returns:
            str: The class name of the task.
        """
        return self.__class__.__name__

    def __eq__(self, other: "TaskNode") -> bool:
        """Checks if this is equal to the other item.

        Arguments:
            other (TaskNode): The other object to compare equality with.

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

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
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


def get_task_execution_order(enforced_task_order: list[TaskNode]) -> list[TaskNode]:
    """Gets the order that tasks should be executed in."""
    execution_order: list[TaskNode] = []
    tasks_added: set[TaskNode] = set()
    for task in enforced_task_order:
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
    """Builds the DAG required for a task and runs the DAG."""
    task_execution_order = get_task_execution_order(enforced_task_order=tasks)
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
    """Converts a list of any arguments into strings."""
    return [str(x) for x in args]


def concatenate_args(args: list[Any | list[Any]]) -> list[str]:
    """Flattens str and list[str] into a single list."""
    all_args_as_lists = [arg if isinstance(arg, list) else [arg] for arg in args]
    return get_str_args(list(itertools.chain.from_iterable(all_args_as_lists)))


def resolve_process_results(
    command_as_str: str,
    output: bytes,
    error: bytes,
    return_code: int,
    silent: bool = False,
) -> None:
    """Prints outputs and errors and exits as appropriate when a command exits."""
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
def demote_process_to_user(user_uid: int, user_gid: int):
    """Creates a function that changes the user."""

    def demote_to_specific_user():
        setgid(user_gid)
        setuid(user_uid)
        environ["HOME"] = f"/home/{getpwuid(user_uid)[0]}/"

    return demote_to_specific_user


def run_process(
    args: list[Any], local_user_uid: int = 0, local_user_gid: int = 0, silent=False
) -> bytes:
    """Runs a process."""
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
    """Runs a process and gets the output."""
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
    """Runs piped processes as they would be on the command line."""
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
