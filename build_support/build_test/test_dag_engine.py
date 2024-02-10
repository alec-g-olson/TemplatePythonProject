import sys
from pathlib import Path
from subprocess import PIPE
from unittest.mock import MagicMock, call, patch

import pytest
from dag_engine import (
    TaskNode,
    concatenate_args,
    get_output_of_process,
    get_str_args,
    get_task_execution_order,
    resolve_process_results,
    run_piped_processes,
    run_process,
    run_process_as_local_user,
    run_tasks,
)


def build_mock_task(task_name: str, required_mock_tasks: list[TaskNode]) -> TaskNode:
    """Builds a mock task for testing task interactions."""
    mock_task = MagicMock(TaskNode)
    mock_task.task_label.return_value = task_name
    mock_task.required_tasks.return_value = required_mock_tasks
    return mock_task


@pytest.fixture
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


@pytest.fixture
def all_task_lookup(all_tasks) -> dict[str, TaskNode]:
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
def run_info(request) -> list[list[str]]:
    return request.param


@pytest.fixture
def tasks_requested(run_info, all_task_lookup) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[0]]


@pytest.fixture
def task_execution_order(run_info, all_task_lookup) -> list[TaskNode]:
    return [all_task_lookup[task_name] for task_name in run_info[1]]


def test_add_task_and_all_required_tasks_to_dict(
    tasks_requested: list[TaskNode],
    task_execution_order: list[TaskNode],
):
    observed_results = get_task_execution_order(enforced_task_order=tasks_requested)
    assert observed_results == task_execution_order


def test_run_tasks(
    tasks_requested: list[TaskNode],
    task_execution_order: list[TaskNode],
    all_tasks: set[TaskNode],
    mock_project_root: Path,
    docker_project_root: Path,
    local_username: str,
):
    run_tasks(
        tasks=tasks_requested,
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_username=local_username,
    )
    for mock_task in all_tasks:
        if mock_task in task_execution_order:
            # MagicMock and mypy aren't playing nice.
            mock_task.run.assert_called_once_with(  # type: ignore
                non_docker_project_root=mock_project_root,
                docker_project_root=docker_project_root,
                local_username=local_username,
            )
        else:
            # MagicMock and mypy aren't playing nice.
            assert mock_task.run.call_count == 0  # type: ignore


def test_get_str_args():
    assert get_str_args(args=[9, 3.5, Path("/usr/dev"), "A string!!!"]) == [
        "9",
        "3.5",
        "/usr/dev",
        "A string!!!",
    ]


def test_concatenate_args():
    assert concatenate_args(args=["a", Path("/usr/dev"), 9, [], [9, 3.5]]) == [
        "a",
        "/usr/dev",
        "9",
        "9",
        "3.5",
    ]


def test_resolve_process_results_normal_process():
    with patch("builtins.print") as mock_print:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with("output", flush=True, end="")


def test_resolve_process_results_normal_process_exit_1():
    with patch("builtins.print") as mock_print, patch("builtins.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"",
            return_code=1,
            silent=False,
        )
        mock_print.assert_called_once_with("output", flush=True, end="")
        mock_exit.assert_called_once_with(1)


def test_resolve_process_results_normal_process_has_error_text():
    with patch("builtins.print") as mock_print:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        assert mock_print.call_count == 2
        mock_print.assert_has_calls(
            calls=[
                call("output", flush=True, end=""),
                call("error", flush=True, end="", file=sys.stderr),
            ]
        )


def test_resolve_process_results_normal_process_has_error_text_exit_1():
    with patch("builtins.print") as mock_print, patch("builtins.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            silent=False,
        )
        assert mock_print.call_count == 2
        mock_print.assert_has_calls(
            calls=[
                call("output", flush=True, end=""),
                call("error", flush=True, end="", file=sys.stderr),
            ]
        )
        mock_exit.assert_called_once_with(1)


def test_resolve_process_results_normal_process_silent():
    with patch("builtins.print") as mock_print:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        assert mock_print.call_count == 1
        mock_print.assert_called_once_with("error", flush=True, end="", file=sys.stderr)


def test_resolve_process_results_normal_process_silent_exit_1():
    with patch("builtins.print") as mock_print, patch("builtins.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            silent=True,
        )
        assert mock_print.call_count == 2
        mock_print.assert_has_calls(
            calls=[
                call("error", flush=True, end="", file=sys.stderr),
                call("run a process\nFailed with code: 1", flush=True, file=sys.stderr),
            ]
        )
        mock_exit.assert_called_once_with(1)


def test_run_process():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert run_process(args=["command", 0, 1.5, Path("/usr/dev")]) == b"output"
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )


def test_run_process_silent():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(args=["command", 0, 1.5, Path("/usr/dev")], silent=True)
            == b"output"
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )


def test_run_process_as_local_user():
    with patch("dag_engine.os.system") as mock_system_call, patch(
        "builtins.print"
    ) as mock_print:
        mock_system_call.return_value = 0
        expected_command = 'su username -c "command 0 1.5 /usr/dev"'
        run_process_as_local_user(
            args=["command", 0, 1.5, Path("/usr/dev")], local_username="username"
        )
        mock_print.assert_called_once_with(expected_command)
        mock_system_call.assert_called_once_with(expected_command)


def test_run_process_as_local_user_exit():
    with patch("dag_engine.os.system") as mock_system_call, patch(
        "builtins.print"
    ) as mock_print, patch("builtins.exit") as mock_exit:
        mock_system_call.return_value = 1
        expected_command = 'su username -c "command 0 1.5 /usr/dev"'
        run_process_as_local_user(
            args=["command", 0, 1.5, Path("/usr/dev")], local_username="username"
        )
        mock_print.assert_called_once_with(expected_command)
        mock_system_call.assert_called_once_with(expected_command)
        mock_exit.assert_called_once_with(1)


def test_run_process_as_local_user_silent():
    with patch("dag_engine.os.system") as mock_system_call:
        mock_system_call.return_value = 0
        expected_command = 'su username -c "command 0 1.5 /usr/dev"'
        run_process_as_local_user(
            args=["command", 0, 1.5, Path("/usr/dev")],
            local_username="username",
            silent=True,
        )
        mock_system_call.assert_called_once_with(expected_command)


def test_get_output_of_process():
    with patch("dag_engine.run_process") as mock_run_process:
        mock_run_process.return_value = b"output"
        assert (
            get_output_of_process(args=["command", 0, 1.5, Path("/usr/dev")])
            == "output"
        )


def test_run_piped_processes():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "builtins.print"
    ) as mock_print, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]]
        )
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        assert mock_popen.call_count == 2
        mock_popen.assert_has_calls(
            calls=[
                call(args=["command", "0", "1.5", "/usr/dev"], stdout=PIPE),
                call(
                    args=["second_command", "1337"],
                    stdin=process_mock.stdout,
                    stdout=PIPE,
                ),
            ]
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_silent():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "builtins.print"
    ) as mock_print, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
            silent=True,
        )
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        assert mock_popen.call_count == 2
        mock_popen.assert_has_calls(
            calls=[
                call(args=["command", "0", "1.5", "/usr/dev"], stdout=PIPE),
                call(
                    args=["second_command", "1337"],
                    stdin=process_mock.stdout,
                    stdout=PIPE,
                ),
            ]
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        mock_print.assert_not_called()


def test_run_piped_processes_one_process():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "builtins.print"
    ) as mock_print, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(processes=[["command", 0, 1.5, Path("/usr/dev")]])
        command_as_str = "command 0 1.5 /usr/dev"
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"], stdout=PIPE
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_one_process_silent():
    with patch("dag_engine.Popen") as mock_popen, patch(
        "builtins.print"
    ) as mock_print, patch(
        "dag_engine.resolve_process_results"
    ) as mock_resolve_process_results:
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")]], silent=True
        )
        command_as_str = "command 0 1.5 /usr/dev"
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"], stdout=PIPE
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        mock_print.assert_not_called()
