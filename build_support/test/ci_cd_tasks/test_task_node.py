from unittest.mock import MagicMock

from build_support.ci_cd_tasks.task_node import TaskNode


def build_mock_task(task_name: str, required_mock_tasks: list[TaskNode]) -> TaskNode:
    """Builds a mock task for testing task interactions."""
    mock_task = MagicMock(TaskNode)
    mock_task.task_label.return_value = task_name
    mock_task.required_tasks.return_value = required_mock_tasks
    mock_task.__hash__ = TaskNode.__hash__  # type: ignore[assignment]
    mock_task.__eq__ = TaskNode.__eq__  # type: ignore[assignment]
    return mock_task


def test_task_hash() -> None:
    task_name = "test_task_hash"
    mock_task = build_mock_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task.__hash__() == hash(mock_task.task_label())


def test_task_eq() -> None:
    task_name = "test_task_eq"
    mock_task_1 = build_mock_task(task_name=task_name, required_mock_tasks=[])
    mock_task_2 = build_mock_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task_1 == mock_task_2


def test_task_ne() -> None:
    mock_task_1 = build_mock_task(task_name="task_1", required_mock_tasks=[])
    mock_task_2 = build_mock_task(task_name="task_2", required_mock_tasks=[])
    assert mock_task_1 != mock_task_2