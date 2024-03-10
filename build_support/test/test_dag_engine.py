import sys
from pathlib import Path
from subprocess import PIPE
from unittest.mock import MagicMock, call, patch

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.env_setup_tasks import Clean
from build_support.dag_engine import (
    TaskNode,
    concatenate_args,
    get_output_of_process,
    get_str_args,
    get_task_execution_order,
    resolve_process_results,
    run_piped_processes,
    run_process,
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


def test_task_hash() -> None:
    task = Clean(
        non_docker_project_root=Path(),
        docker_project_root=Path(),
        local_user_uid=0,
        local_user_gid=0,
    )
    assert task.__hash__() == hash(task.task_label())


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


def test_get_str_args() -> None:
    assert get_str_args(args=[9, 3.5, Path("/usr/dev"), "A string!!!"]) == [
        "9",
        "3.5",
        "/usr/dev",
        "A string!!!",
    ]


def test_concatenate_args() -> None:
    assert concatenate_args(args=["a", Path("/usr/dev"), 9, [], [9, 3.5]]) == [
        "a",
        "/usr/dev",
        "9",
        "9",
        "3.5",
    ]


def test_resolve_process_results_normal_process() -> None:
    with patch("builtins.print") as mock_print:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with("output", flush=True, end="")


def test_resolve_process_results_normal_process_exit_1() -> None:
    with (
        patch("builtins.print") as mock_print,
        patch("build_support.dag_engine.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"",
            return_code=1,
            silent=False,
        )
        mock_print.assert_called_once_with("output", flush=True, end="")
        mock_exit.assert_called_once_with(1)


def test_resolve_process_results_normal_process_has_error_text() -> None:
    with patch("builtins.print") as mock_print:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        expected_print_calls = [
            call("output", flush=True, end=""),
            call("error", flush=True, end="", file=sys.stderr),
        ]
        assert mock_print.call_count == len(expected_print_calls)
        mock_print.assert_has_calls(calls=expected_print_calls)


def test_resolve_process_results_normal_process_has_error_text_exit_1() -> None:
    with (
        patch("builtins.print") as mock_print,
        patch("build_support.dag_engine.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            silent=False,
        )
        expected_print_calls = [
            call("output", flush=True, end=""),
            call("error", flush=True, end="", file=sys.stderr),
        ]
        assert mock_print.call_count == len(expected_print_calls)
        mock_print.assert_has_calls(calls=expected_print_calls)
        mock_exit.assert_called_once_with(1)


def test_resolve_process_results_normal_process_silent() -> None:
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


def test_resolve_process_results_normal_process_silent_exit_1() -> None:
    with (
        patch("builtins.print") as mock_print,
        patch("build_support.dag_engine.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            silent=True,
        )
        expected_print_calls = [
            call("error", flush=True, end="", file=sys.stderr),
            call("run a process\nFailed with code: 1", flush=True, file=sys.stderr),
        ]
        assert mock_print.call_count == len(expected_print_calls)
        mock_print.assert_has_calls(calls=expected_print_calls)
        mock_exit.assert_called_once_with(1)


def test_run_process() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert run_process(args=["command", 0, 1.5, Path("/usr/dev")]) == b"output"
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=None,
            group=None,
            env=None,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )


def test_run_process_silent() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(args=["command", 0, 1.5, Path("/usr/dev")], silent=True)
            == b"output"
        )
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=None,
            group=None,
            env=None,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )


def test_run_process_as_user() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.dag_engine.getpwuid") as mock_getpwuid,
        patch(
            "build_support.dag_engine.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = [user_name]
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(
                args=["command", 0, 1.5, Path("/usr/dev")],
                user_uid=1337,
                user_gid=42,
            )
            == b"output"
        )
        assert len(mock_environ) == 1
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=1337,
            group=42,
            env=expected_new_env,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )


def test_run_process_silent_as_user() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.dag_engine.getpwuid") as mock_getpwuid,
        patch(
            "build_support.dag_engine.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = [user_name]
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(
                args=["command", 0, 1.5, Path("/usr/dev")],
                user_uid=1337,
                user_gid=42,
                silent=True,
            )
            == b"output"
        )
        assert len(mock_environ) == 1
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=1337,
            group=42,
            env=expected_new_env,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )


def test_get_output_of_process() -> None:
    with patch("build_support.dag_engine.run_process") as mock_run_process:
        mock_run_process.return_value = b"output"
        assert (
            get_output_of_process(args=["command", 0, 1.5, Path("/usr/dev")])
            == "output"
        )


def test_run_piped_processes() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
        )
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                user=None,
                group=None,
                env=None,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
                user=None,
                group=None,
                env=None,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_silent() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
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
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                user=None,
                group=None,
                env=None,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
                user=None,
                group=None,
                env=None,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        mock_print.assert_not_called()


def test_run_piped_processes_as_user() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.dag_engine.getpwuid") as mock_getpwuid,
        patch(
            "build_support.dag_engine.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = [user_name]
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
            user_uid=1337,
            user_gid=42,
        )
        assert len(mock_environ) == 1
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                user=1337,
                group=42,
                env=expected_new_env,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
                user=1337,
                group=42,
                env=expected_new_env,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_silent_as_user() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.dag_engine.getpwuid") as mock_getpwuid,
        patch(
            "build_support.dag_engine.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = [user_name]
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
            user_uid=1337,
            user_gid=42,
            silent=True,
        )
        assert len(mock_environ) == 1
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                user=1337,
                group=42,
                env=expected_new_env,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
                user=1337,
                group=42,
                env=expected_new_env,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        mock_print.assert_not_called()


def test_run_piped_processes_one_process() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(processes=[["command", 0, 1.5, Path("/usr/dev")]])
        command_as_str = "command 0 1.5 /usr/dev"
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=None,
            group=None,
            env=None,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=False,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_one_process_silent() -> None:
    with (
        patch("build_support.dag_engine.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.dag_engine.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = MagicMock()
        process_mock.communicate = MagicMock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")]],
            silent=True,
        )
        command_as_str = "command 0 1.5 /usr/dev"
        mock_popen.assert_called_once_with(
            args=["command", "0", "1.5", "/usr/dev"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
            user=None,
            group=None,
            env=None,
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
            silent=True,
        )
        mock_print.assert_not_called()
