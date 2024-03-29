from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.dag_engine import (
    get_task_execution_order,
    run_tasks,
)


def build_mock_task(task_name: str, required_mock_tasks: list[TaskNode]) -> TaskNode:
    """Builds a mock task for testing task interactions."""
    mock_task = MagicMock(TaskNode)
    mock_task.task_label.return_value = task_name
    mock_task.required_tasks.return_value = required_mock_tasks
    return mock_task


@pytest.fixture()
def all_tasks() -> set[TaskNode]:
    task1 = build_mock_task(task_name="TASK_1", required_mock_tasks=[])
    task2 = build_mock_task(task_name="TASK_2", required_mock_tasks=[])
    task3 = build_mock_task(task_name="TASK_3", required_mock_tasks=[task2, task1])
    task4 = build_mock_task(task_name="TASK_4", required_mock_tasks=[task1, task3])
    task5 = build_mock_task(task_name="TASK_5", required_mock_tasks=[])
    task6 = build_mock_task(task_name="TASK_6", required_mock_tasks=[task5])
    task7 = build_mock_task(task_name="TASK_7", required_mock_tasks=[task5])
    task8 = build_mock_task(task_name="TASK_8", required_mock_tasks=[task2, task7])
    task9 = build_mock_task(task_name="TASK_9", required_mock_tasks=[task8, task4])
    return {task1, task2, task3, task4, task5, task6, task7, task8, task9}


@pytest.fixture()
def all_task_lookup(all_tasks: set[TaskNode]) -> dict[str, TaskNode]:
    return {task.task_label(): task for task in all_tasks}


tasks_names_to_execution_order_names = [
    [["TASK_1"], ["TASK_1"]],
    [["TASK_5", "TASK_6"], ["TASK_5", "TASK_6"]],
    [["TASK_6", "TASK_5"], ["TASK_5", "TASK_6"]],
    [["TASK_3", "TASK_4"], ["TASK_2", "TASK_1", "TASK_3", "TASK_4"]],
    [["TASK_4", "TASK_3"], ["TASK_1", "TASK_2", "TASK_3", "TASK_4"]],
    [
        ["TASK_3", "TASK_5", "TASK_6", "TASK_7"],
        ["TASK_2", "TASK_1", "TASK_3", "TASK_5", "TASK_6", "TASK_7"],
    ],
    [
        ["TASK_7", "TASK_6", "TASK_3", "TASK_5"],
        ["TASK_5", "TASK_7", "TASK_6", "TASK_2", "TASK_1", "TASK_3"],
    ],
    [
        ["TASK_4", "TASK_8"],
        ["TASK_1", "TASK_2", "TASK_3", "TASK_4", "TASK_5", "TASK_7", "TASK_8"],
    ],
    [
        ["TASK_8", "TASK_4"],
        ["TASK_2", "TASK_5", "TASK_7", "TASK_8", "TASK_1", "TASK_3", "TASK_4"],
    ],
    [
        ["TASK_9"],
        [
            "TASK_2",
            "TASK_5",
            "TASK_7",
            "TASK_8",
            "TASK_1",
            "TASK_3",
            "TASK_4",
            "TASK_9",
        ],
    ],
    [
        ["TASK_4", "TASK_9"],
        [
            "TASK_1",
            "TASK_2",
            "TASK_3",
            "TASK_4",
            "TASK_5",
            "TASK_7",
            "TASK_8",
            "TASK_9",
        ],
    ],
]


@pytest.fixture(params=tasks_names_to_execution_order_names)
def run_info(request: SubRequest) -> list[list[str]]:
    return request.param


@pytest.fixture()
def tasks_requested(
    run_info: list[list[str]], all_task_lookup: dict[str, TaskNode]
) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[0]]


@pytest.fixture()
def task_execution_order(
    run_info: list[list[str]], all_task_lookup: dict[str, TaskNode]
) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[1]]


def test_add_task_and_all_required_tasks_to_dict(
    tasks_requested: list[TaskNode],
    task_execution_order: list[TaskNode],
) -> None:
    observed_results = get_task_execution_order(requested_tasks=tasks_requested)
    assert observed_results == task_execution_order


def test_run_tasks(
    tasks_requested: list[TaskNode],
    task_execution_order: list[TaskNode],
    all_tasks: set[TaskNode],
) -> None:
    run_tasks(tasks=tasks_requested)
    for mock_task in all_tasks:
        # need this line to make MyPy play nice with MagicMock
        if isinstance(mock_task, MagicMock):
            if mock_task in task_execution_order:
                mock_task.run.assert_called_once_with()
            else:
                assert mock_task.run.call_count == 0
        else:  # pragma: no cover - not hit if test passes
            pytest.fail("Something when wrong in test setup.")
