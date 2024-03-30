import sys
from pathlib import Path
from subprocess import PIPE
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from build_support.process_runner import (
    ProcessVerbosity,
    concatenate_args,
    get_output_of_process,
    get_str_args,
    resolve_process_results,
    run_piped_processes,
    run_process,
)


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
            verbosity=ProcessVerbosity.ALL,
        )
        mock_print.assert_called_once_with("output", flush=True, end="")


def test_resolve_process_results_normal_process_exit_1() -> None:
    with (
        patch("builtins.print") as mock_print,
        patch("build_support.process_runner.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"",
            return_code=1,
            verbosity=ProcessVerbosity.ALL,
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
            verbosity=ProcessVerbosity.ALL,
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
        patch("build_support.process_runner.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            verbosity=ProcessVerbosity.ALL,
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
            verbosity=ProcessVerbosity.SILENT,
        )
        assert mock_print.call_count == 1
        mock_print.assert_called_once_with("error", flush=True, end="", file=sys.stderr)


def test_resolve_process_results_normal_process_silent_exit_1() -> None:
    with (
        patch("builtins.print") as mock_print,
        patch("build_support.process_runner.sys.exit") as mock_exit,
    ):
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
            verbosity=ProcessVerbosity.SILENT,
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
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
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
            verbosity=ProcessVerbosity.ALL,
        )


def test_run_process_silent() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(
                args=["command", 0, 1.5, Path("/usr/dev")],
                verbosity=ProcessVerbosity.SILENT,
            )
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
            verbosity=ProcessVerbosity.SILENT,
        )


def test_run_process_as_user() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.process_runner.getpwuid") as mock_getpwuid,
        patch(
            "build_support.process_runner.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = SimpleNamespace(pw_name=user_name)
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = Mock()
        process_mock.communicate = Mock()
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
            verbosity=ProcessVerbosity.ALL,
        )


def test_run_process_silent_as_user() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.process_runner.getpwuid") as mock_getpwuid,
        patch(
            "build_support.process_runner.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = SimpleNamespace(pw_name=user_name)
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        assert (
            run_process(
                args=["command", 0, 1.5, Path("/usr/dev")],
                user_uid=1337,
                user_gid=42,
                verbosity=ProcessVerbosity.SILENT,
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
            verbosity=ProcessVerbosity.SILENT,
        )


def test_get_output_of_process() -> None:
    with patch("build_support.process_runner.run_process") as mock_run_process:
        mock_run_process.return_value = b"output"
        assert (
            get_output_of_process(args=["command", 0, 1.5, Path("/usr/dev")])
            == "output"
        )


def test_run_piped_processes() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
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
            verbosity=ProcessVerbosity.ALL,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_silent() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
            verbosity=ProcessVerbosity.SILENT,
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
            verbosity=ProcessVerbosity.SILENT,
        )
        mock_print.assert_not_called()


def test_run_piped_processes_as_user() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.process_runner.getpwuid") as mock_getpwuid,
        patch(
            "build_support.process_runner.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = SimpleNamespace(pw_name=user_name)
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = Mock()
        process_mock.communicate = Mock()
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
            verbosity=ProcessVerbosity.ALL,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_silent_as_user() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
        patch("build_support.process_runner.getpwuid") as mock_getpwuid,
        patch(
            "build_support.process_runner.environ", {"initial_key": "initial_val"}
        ) as mock_environ,
    ):
        user_name = "user_name"
        mock_getpwuid.return_value = SimpleNamespace(pw_name=user_name)
        home_path = f"/home/{user_name}/"
        expected_new_env = mock_environ.copy()
        expected_new_env["HOME"] = home_path
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]],
            user_uid=1337,
            user_gid=42,
            verbosity=ProcessVerbosity.SILENT,
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
            verbosity=ProcessVerbosity.SILENT,
        )
        mock_print.assert_not_called()


def test_run_piped_processes_one_process() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
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
            verbosity=ProcessVerbosity.ALL,
        )
        mock_print.assert_called_once_with(command_as_str, flush=True)


def test_run_piped_processes_one_process_silent() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.process_runner.resolve_process_results",
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")]],
            verbosity=ProcessVerbosity.SILENT,
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
            verbosity=ProcessVerbosity.SILENT,
        )
        mock_print.assert_not_called()
