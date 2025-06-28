from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
import yaml
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.task_node import BasicTaskInfo, TaskNode
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_runtime_report_path,
)
from build_support.dag_engine import BuildRunReport, get_task_execution_order, run_tasks


def build_mock_basic_task(
    task_name: str, required_mock_tasks: list[TaskNode]
) -> TaskNode:
    """Builds a mock task for testing task interactions."""

    return type(  # type: ignore[no-any-return]
        task_name,
        (TaskNode,),
        {"required_tasks": Mock(return_value=required_mock_tasks), "run": Mock()},
    )(
        basic_task_info=BasicTaskInfo(
            non_docker_project_root=Path("/root"),
            docker_project_root=Path("/root"),
            local_uid=10,
            local_gid=2,
            local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
        )
    )


@pytest.fixture
def all_tasks() -> set[TaskNode]:
    task1 = build_mock_basic_task(task_name="TASK_1", required_mock_tasks=[])
    task2 = build_mock_basic_task(task_name="TASK_2", required_mock_tasks=[])
    task3 = build_mock_basic_task(
        task_name="TASK_3", required_mock_tasks=[task2, task1]
    )
    task4 = build_mock_basic_task(
        task_name="TASK_4", required_mock_tasks=[task1, task3]
    )
    task5 = build_mock_basic_task(task_name="TASK_5", required_mock_tasks=[])
    task6 = build_mock_basic_task(task_name="TASK_6", required_mock_tasks=[task5])
    task7 = build_mock_basic_task(task_name="TASK_7", required_mock_tasks=[task5])
    task8 = build_mock_basic_task(
        task_name="TASK_8", required_mock_tasks=[task2, task7]
    )
    task9 = build_mock_basic_task(
        task_name="TASK_9", required_mock_tasks=[task8, task4]
    )
    return {task1, task2, task3, task4, task5, task6, task7, task8, task9}


@pytest.fixture
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
    return cast(list[list[str]], request.param)


@pytest.fixture
def tasks_requested(
    run_info: list[list[str]], all_task_lookup: dict[str, TaskNode]
) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[0]]


@pytest.fixture
def task_execution_order(
    run_info: list[list[str]], all_task_lookup: dict[str, TaskNode]
) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[1]]


def test_add_task_and_all_required_tasks_to_dict(
    tasks_requested: list[TaskNode], task_execution_order: list[TaskNode]
) -> None:
    observed_results = get_task_execution_order(requested_tasks=tasks_requested)
    assert observed_results == task_execution_order


def test_run_tasks(
    tasks_requested: list[TaskNode],
    task_execution_order: list[TaskNode],
    all_tasks: set[TaskNode],
    mock_project_root: Path,
) -> None:
    run_tasks(tasks=tasks_requested, project_root=mock_project_root)
    for task in all_tasks:
        task_run = task.run
        if isinstance(task_run, Mock):
            if task in task_execution_order:
                task_run.assert_called_once_with()
            else:
                assert task_run.run.call_count == 0
        else:  # pragma: no cov - will only hit if setup incorrectly
            pytest.fail("This test was setup incorrectly, task.run should be a mock.")
    parsed_report = BuildRunReport.from_yaml(
        get_build_runtime_report_path(project_root=mock_project_root).read_text()
    )
    assert len(parsed_report.report) == len(task_execution_order)


@pytest.fixture
def build_runtime_report_data() -> dict[str, list[dict[str, str]]]:
    return {
        "report": [
            {"duration": "0:00:00.000036", "task_name": "TASK_5"},
            {"duration": "0:00:00.000024", "task_name": "TASK_6"},
        ]
    }


@pytest.fixture
def build_runtime_report_yaml_str(
    build_runtime_report_data: dict[str, list[dict[str, str]]],
) -> str:
    return yaml.dump(build_runtime_report_data)


def test_load_build_runtime_report(
    build_runtime_report_yaml_str: str,
    build_runtime_report_data: dict[str, list[dict[str, str]]],
) -> None:
    build_runtime_report = BuildRunReport.from_yaml(
        yaml_str=build_runtime_report_yaml_str
    )
    assert build_runtime_report == BuildRunReport.model_validate(
        build_runtime_report_data
    )


def test_dump_build_runtime_report(
    build_runtime_report_yaml_str: str,
    build_runtime_report_data: dict[str, list[dict[str, str]]],
) -> None:
    build_runtime_report = BuildRunReport.model_validate(build_runtime_report_data)
    assert build_runtime_report.to_yaml() == build_runtime_report_yaml_str
