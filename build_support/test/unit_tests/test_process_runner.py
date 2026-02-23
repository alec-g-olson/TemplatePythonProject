import logging
from pathlib import Path
from subprocess import PIPE
from unittest.mock import Mock, call, patch

import pytest
from build_support.process_runner import (
    TRACE,
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


def test_resolve_process_results_normal_process(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(TRACE, logger="build_support.process_runner")
    resolve_process_results(
        command_as_str="run a process", output=b"output", error=b"", return_code=0
    )
    assert "output" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == TRACE


def test_resolve_process_results_normal_process_exit_1(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="build_support.process_runner")
    with patch("build_support.process_runner.sys.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process", output=b"output", error=b"", return_code=1
        )
    assert "output" in caplog.text
    assert "Failed with code: 1" in caplog.text
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    expected_error_count = 2
    assert len(error_records) == expected_error_count
    mock_exit.assert_called_once_with(1)


def test_resolve_process_results_normal_process_has_error_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(TRACE, logger="build_support.process_runner")
    resolve_process_results(
        command_as_str="run a process", output=b"output", error=b"error", return_code=0
    )
    assert "output" in caplog.text
    assert "error" in caplog.text
    expected_trace_count = 2
    assert len(caplog.records) == expected_trace_count
    assert all(r.levelno == TRACE for r in caplog.records)


def test_resolve_process_results_success_stderr_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(TRACE, logger="build_support.process_runner")
    resolve_process_results(
        command_as_str="run a process", output=b"", error=b"stderr only", return_code=0
    )
    assert "stderr only" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == TRACE


def test_resolve_process_results_normal_process_has_error_text_exit_1(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="build_support.process_runner")
    with patch("build_support.process_runner.sys.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process",
            output=b"output",
            error=b"error",
            return_code=1,
        )
    assert "output" in caplog.text
    assert "error" in caplog.text
    assert "Failed with code: 1" in caplog.text
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    expected_error_count = 3
    assert len(error_records) == expected_error_count
    mock_exit.assert_called_once_with(1)


def test_resolve_process_results_failure_stderr_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="build_support.process_runner")
    with patch("build_support.process_runner.sys.exit") as mock_exit:
        resolve_process_results(
            command_as_str="run a process",
            output=b"",
            error=b"stderr only",
            return_code=1,
        )
    assert "Failed with code: 1" in caplog.text
    assert "stderr only" in caplog.text
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    expected_error_count = 2
    assert len(error_records) == expected_error_count
    mock_exit.assert_called_once_with(1)


def test_resolve_process_results_at_info_level_suppresses_trace_output(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """At INFO level, stdout/stderr are not logged (TRACE only)."""
    caplog.set_level(logging.INFO, logger="build_support.process_runner")
    resolve_process_results(
        command_as_str="run a process", output=b"output", error=b"error", return_code=0
    )
    assert "output" not in caplog.text
    assert "error" not in caplog.text
    assert len(caplog.records) == 0


def test_run_process() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results"
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
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str="command 0 1.5 /usr/dev",
            output=b"output",
            error=b"error",
            return_code=0,
        )


def test_get_output_of_process() -> None:
    with patch("build_support.process_runner.run_process") as mock_run_process:
        mock_run_process.return_value = b"output"
        assert (
            get_output_of_process(args=["command", 0, 1.5, Path("/usr/dev")])
            == "output"
        )


def test_run_piped_processes(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="build_support.process_runner")
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results"
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]]
        )
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
        )
        assert command_as_str in caplog.text


def test_run_piped_processes_silent() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results"
        ) as mock_resolve_process_results,
    ):
        process_mock = Mock()
        process_mock.communicate = Mock()
        process_mock.communicate.return_value = b"output", b"error"
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        run_piped_processes(
            processes=[["command", 0, 1.5, Path("/usr/dev")], ["second_command", 1337]]
        )
        command_as_str = "command 0 1.5 /usr/dev | second_command 1337"
        expected_popen_calls = [
            call(
                args=["command", "0", "1.5", "/usr/dev"],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
            ),
            call(
                args=["second_command", "1337"],
                stdin=process_mock.stdout,
                stdout=PIPE,
                stderr=PIPE,
            ),
        ]
        assert mock_popen.call_count == len(expected_popen_calls)
        mock_popen.assert_has_calls(calls=expected_popen_calls)
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
        )


def test_run_piped_processes_one_process(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="build_support.process_runner")
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results"
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
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
        )
        assert command_as_str in caplog.text


def test_run_piped_processes_one_process_silent() -> None:
    with (
        patch("build_support.process_runner.Popen") as mock_popen,
        patch(
            "build_support.process_runner.resolve_process_results"
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
        )
        mock_resolve_process_results.assert_called_once_with(
            command_as_str=command_as_str,
            output=b"output",
            error=b"error",
            return_code=0,
        )
