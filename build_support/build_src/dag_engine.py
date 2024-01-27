"""Shared logic across all tasks and how to run them in a DAG."""

import itertools
from abc import ABC, abstractmethod
from pathlib import Path
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
    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Will contain the logic of each task."""


def _build_dict_of_all_dag_tasks(
    all_tasks: dict[str, TaskNode], task_to_add: TaskNode
) -> None:
    if task_to_add.task_label() not in all_tasks:
        all_tasks[task_to_add.task_label()] = task_to_add
        for required_task in task_to_add.required_tasks():
            _build_dict_of_all_dag_tasks(all_tasks=all_tasks, task_to_add=required_task)


def _add_tasks_to_list_with_dfs(
    execution_order: list[TaskNode],
    task_names_added: set[str],
    task_name_to_required_names: dict[str, list[str]],
    task_to_add: TaskNode,
) -> None:
    if task_to_add.task_label() not in task_names_added:
        for required_task in task_to_add.required_tasks():
            _add_tasks_to_list_with_dfs(
                execution_order=execution_order,
                task_names_added=task_names_added,
                task_name_to_required_names=task_name_to_required_names,
                task_to_add=required_task,
            )
        task_names_added.add(task_to_add.task_label())
        execution_order.append(task_to_add)


def _get_task_execution_order(
    all_tasks: dict[str, TaskNode], enforced_task_order: list[TaskNode]
) -> list[TaskNode]:
    execution_order: list[TaskNode] = []
    task_names_added: set[str] = set()
    task_name_to_required_names = {
        task.task_label(): [
            required_task.task_label() for required_task in task.required_tasks()
        ]
        for task in all_tasks.values()
    }
    for task in enforced_task_order:
        _add_tasks_to_list_with_dfs(
            execution_order=execution_order,
            task_names_added=task_names_added,
            task_name_to_required_names=task_name_to_required_names,
            task_to_add=task,
        )
    return execution_order


def run_tasks(
    tasks: list[TaskNode], non_docker_project_root: Path, docker_project_root: Path
) -> None:
    """Builds the DAG required for a task and runs the DAG."""
    all_dag_tasks: dict[str, TaskNode] = {}
    for task in tasks:
        _build_dict_of_all_dag_tasks(all_tasks=all_dag_tasks, task_to_add=task)
    task_execution_order = _get_task_execution_order(
        all_tasks=all_dag_tasks, enforced_task_order=tasks
    )
    print("Will execute the following tasks:")
    for task in task_execution_order:
        print(f"  - {task.task_label()}")
    for task in task_execution_order:
        print(f"Starting: {task.task_label()}")
        task.run(
            non_docker_project_root=non_docker_project_root,
            docker_project_root=docker_project_root,
        )


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
