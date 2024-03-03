from pathlib import Path
from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import SetupDevEnvironment
from build_support.ci_cd_tasks.lint_tasks import (
    ApplyRuffFixUnsafe,
    Lint,
    RuffFixSafe,
)
from build_support.ci_cd_tasks.validation_tasks import (
    ValidateBuildSupport,
    ValidatePypi,
)
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_test_folders,
    get_all_python_folders,
    get_all_test_folders,
)
from build_support.dag_engine import concatenate_args


@pytest.fixture()
def lint_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> Lint:
    return Lint(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_lint_requires(lint_task: Lint) -> None:
    assert lint_task.required_tasks() == [
        SetupDevEnvironment(
            non_docker_project_root=lint_task.non_docker_project_root,
            docker_project_root=lint_task.docker_project_root,
            local_user_uid=lint_task.local_user_uid,
            local_user_gid=lint_task.local_user_gid,
        )
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_lint(lint_task: Lint) -> None:
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        sort_imports_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=lint_task.non_docker_project_root,
                    docker_project_root=lint_task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--select",
                "I",
                "--fix",
                get_all_python_folders(project_root=lint_task.docker_project_root),
            ],
        )
        format_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=lint_task.non_docker_project_root,
                    docker_project_root=lint_task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "format",
                get_all_python_folders(project_root=lint_task.docker_project_root),
            ],
        )
        lint_task.run()
        expected_run_process_calls = [
            call(args=sort_imports_args),
            call(args=format_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


@pytest.fixture()
def ruff_fix_safe_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> RuffFixSafe:
    return RuffFixSafe(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_ruff_fix_safe_requires(ruff_fix_safe_task: RuffFixSafe) -> None:
    assert ruff_fix_safe_task.required_tasks() == [
        Lint(
            non_docker_project_root=ruff_fix_safe_task.non_docker_project_root,
            docker_project_root=ruff_fix_safe_task.docker_project_root,
            local_user_uid=ruff_fix_safe_task.local_user_uid,
            local_user_gid=ruff_fix_safe_task.local_user_gid,
        ),
        ValidatePypi(
            non_docker_project_root=ruff_fix_safe_task.non_docker_project_root,
            docker_project_root=ruff_fix_safe_task.docker_project_root,
            local_user_uid=ruff_fix_safe_task.local_user_uid,
            local_user_gid=ruff_fix_safe_task.local_user_gid,
        ),
        ValidateBuildSupport(
            non_docker_project_root=ruff_fix_safe_task.non_docker_project_root,
            docker_project_root=ruff_fix_safe_task.docker_project_root,
            local_user_uid=ruff_fix_safe_task.local_user_uid,
            local_user_gid=ruff_fix_safe_task.local_user_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_ruff_fix_safe(ruff_fix_safe_task: RuffFixSafe) -> None:
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        fix_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=ruff_fix_safe_task.non_docker_project_root,
                    docker_project_root=ruff_fix_safe_task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--fix",
                get_all_non_test_folders(
                    project_root=ruff_fix_safe_task.docker_project_root
                ),
            ],
        )
        fix_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=ruff_fix_safe_task.non_docker_project_root,
                    docker_project_root=ruff_fix_safe_task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D",
                "--fix",
                get_all_test_folders(
                    project_root=ruff_fix_safe_task.docker_project_root
                ),
            ],
        )
        ruff_fix_safe_task.run()
        expected_run_process_calls = [
            call(args=fix_src_args),
            call(args=fix_test_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


@pytest.fixture()
def apply_ruff_fix_unsafe_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> ApplyRuffFixUnsafe:
    return ApplyRuffFixUnsafe(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_apply_ruff_fix_unsafe_requires(
    apply_ruff_fix_unsafe_task: ApplyRuffFixUnsafe,
) -> None:
    assert apply_ruff_fix_unsafe_task.required_tasks() == [
        RuffFixSafe(
            non_docker_project_root=apply_ruff_fix_unsafe_task.non_docker_project_root,
            docker_project_root=apply_ruff_fix_unsafe_task.docker_project_root,
            local_user_uid=apply_ruff_fix_unsafe_task.local_user_uid,
            local_user_gid=apply_ruff_fix_unsafe_task.local_user_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_apply_run_ruff_fix_unsafe(
    apply_ruff_fix_unsafe_task: ApplyRuffFixUnsafe,
) -> None:
    task = apply_ruff_fix_unsafe_task
    with patch(
        "build_support.ci_cd_tasks.lint_tasks.run_process"
    ) as run_process_mock, patch(
        "build_support.ci_cd_tasks.lint_tasks.commit_changes_if_diff"
    ) as commit_changes_mock:
        fix_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--fix",
                "--unsafe-fixes",
                get_all_non_test_folders(project_root=task.docker_project_root),
            ],
        )
        fix_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D",
                "--fix",
                "--unsafe-fixes",
                get_all_test_folders(project_root=task.docker_project_root),
            ],
        )
        task.run()
        expected_run_process_calls = [
            call(args=fix_src_args),
            call(args=fix_test_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)
        commit_changes_mock.assert_called_once_with(
            commit_message_no_quotes=(
                "Committing staged changes for before applying unsafe ruff fixes."
            ),
            local_user_uid=task.local_user_uid,
            local_user_gid=task.local_user_gid,
        )
