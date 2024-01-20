"""Shared logic across all tasks and how to run them in a DAG."""
import itertools
from abc import ABC, abstractmethod
from subprocess import PIPE, Popen, run
from typing import Any


class TaskNode(ABC):
    """An abstract representation of a task that can be run in a DAG."""

    def task_label(self) -> str:
        """A unique label for each task, used when building the DAG."""
        return self.__class__.__name__

    @abstractmethod
    def required_tasks(self) -> list["TaskNode"]:
        """Will return the tasks required to start the current task."""

    @abstractmethod
    def run(self) -> None:
        """Will contain the logic of each task."""


def run_task(task: TaskNode) -> None:
    """Builds the DAG required for a task and runs the DAG."""
    tasks = {}
    tasks_to_add = [task]
    reverse_execution_order = []
    for task in tasks_to_add:
        task_label = task.task_label()
        if task_label not in tasks:
            tasks[task_label] = task
            reverse_execution_order.append(task)
            required_tasks = task.required_tasks()
            for required_task in required_tasks:
                if required_task not in tasks:
                    tasks_to_add.append(required_task)
    task_execution_order = list(reversed(reverse_execution_order))
    print("Will execute the following tasks:")
    for task in task_execution_order:
        print(f"  - {task.task_label()}")
    for task in task_execution_order:
        print(f"Starting: {task.task_label()}")
        task.run()


def get_str_args(args: list[Any]) -> list[str]:
    """Converts a list of any arguments into strings."""
    return [str(x) for x in args]


def concatenate_args(args: list[Any | list[Any]]) -> list[str]:
    """Flattens str and list[str] into a single list."""
    all_args_as_lists = [arg if isinstance(arg, list) else [arg] for arg in args]
    return get_str_args(list(itertools.chain.from_iterable(all_args_as_lists)))


def run_process(args: list[Any], silent=False) -> None:
    """Runs a process."""
    args = get_str_args(args=args)
    if not silent:
        print(" ".join(args))
    result = run(args=args)
    if result.returncode != 0:
        exit(result.returncode)


def get_output_of_process(args: list[Any], silent=False) -> str:
    """Runs a process and gets the output."""
    args = get_str_args(args=args)
    if not silent:
        print(" ".join(args))
    p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    output, _ = p.communicate()
    return output.decode("utf-8").strip()


def run_piped_processes(processes: list[list[Any]], silent=False) -> None:
    """Runs piped processes as they would be on the command line."""
    args_list = [get_str_args(args=args) for args in processes]
    process_strs = [" ".join(args) for args in args_list]
    if not silent:
        print(" | ".join(process_strs))
    if len(args_list) == 1:
        result = run(args=processes[0])
        return_code = result.returncode
    else:
        p1 = Popen(args=args_list[0], stdout=PIPE)
        popen_processes = [p1]  # type: ignore
        for args in args_list[1:]:
            last_process = popen_processes[-1]
            popen_processes.append(
                Popen(args=args, stdin=last_process.stdout, stdout=PIPE)  # type: ignore
            )
        popen_processes[-1].communicate()
        return_code = popen_processes[-1].returncode
    if return_code != 0:
        exit(return_code)
