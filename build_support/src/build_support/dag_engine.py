"""Logic for building a DAG of tasks and running them in order."""

from build_support.ci_cd_tasks.task_node import TaskNode


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


def run_tasks(tasks: list[TaskNode]) -> None:
    """Builds the DAG required for a task and runs the DAG.

    Args:
        tasks (list[TaskNode]): Tasks that will be executed, along with prerequisite
            tasks.

    Returns:
        None
    """
    task_execution_order = get_task_execution_order(requested_tasks=tasks)
    print("Will execute the following tasks:", flush=True)  # noqa: T201
    for task in task_execution_order:
        print(f"  - {task.task_label()}", flush=True)  # noqa: T201
    for task in task_execution_order:
        print(f"Starting: {task.task_label()}", flush=True)  # noqa: T201
        task.run()
