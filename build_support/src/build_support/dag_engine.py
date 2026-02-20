"""Logic for building a DAG of tasks and running them in order."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel
from yaml import safe_dump, safe_load

from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_vars.build_paths import get_build_runtime_report_path


def _add_tasks_to_list_with_dfs(
    execution_order: list[TaskNode], tasks_added: set[TaskNode], task_to_add: TaskNode
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
            execution_order=execution_order, tasks_added=tasks_added, task_to_add=task
        )
    return execution_order


class TaskRunReport(BaseModel):
    """An object containing a report of how long a single task took to run."""

    task_name: str
    duration: timedelta


class BuildRunReport(BaseModel):
    """An object containing a report of how long the build took to run."""

    report: list[TaskRunReport] = []

    @staticmethod
    def from_yaml(yaml_str: str) -> "BuildRunReport":
        """Builds an object from a yaml str.

        Args:
            yaml_str (str): String of the YAML representation of a BuildRunReport.

        Returns:
            BuildRunReport: A BuildRunReport object parsed from the YAML.
        """
        return BuildRunReport.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str.

        Returns:
            str: A YAML representation of this BuildRunReport instance.
        """
        return safe_dump(self.model_dump(mode="json"))


def run_tasks(tasks: list[TaskNode], project_root: Path) -> None:
    """Builds the DAG required for a task and runs the DAG.

    Args:
        tasks (list[TaskNode]): Tasks that will be executed, along with prerequisite
            tasks.
        project_root (Path): Path to this project's root.

    Returns:
        None
    """
    run_report = BuildRunReport()
    task_execution_order = get_task_execution_order(requested_tasks=tasks)
    print("Will execute the following tasks:", flush=True)  # noqa: T201
    for task in task_execution_order:
        print(f"  - {task.task_label()}", flush=True)  # noqa: T201
    for task in task_execution_order:
        print(f"Starting: {task.task_label()}", flush=True)  # noqa: T201
        start = datetime.now(tz=UTC)
        task.run()
        duration = datetime.now(tz=UTC) - start
        run_report.report.append(
            TaskRunReport(task_name=task.task_label(), duration=duration)
        )
    report_content = run_report.to_yaml()
    print(report_content)  # noqa: T201
    get_build_runtime_report_path(project_root=project_root).write_text(report_content)
