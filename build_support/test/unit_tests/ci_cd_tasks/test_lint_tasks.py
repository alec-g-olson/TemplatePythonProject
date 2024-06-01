from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import SetupDevEnvironment
from build_support.ci_cd_tasks.lint_tasks import (
    Format,
    Lint,
    LintApplyUnsafeFixes,
)
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import (
    AllSubprojectUnitTests,
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
from build_support.process_runner import concatenate_args


def test_lint_requires(basic_task_info: BasicTaskInfo) -> None:
    assert Format(basic_task_info=basic_task_info).required_tasks() == [
        SetupDevEnvironment(basic_task_info=basic_task_info)
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_lint(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        sort_imports_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--select",
                "I",
                "--fix",
                get_all_python_folders(
                    project_root=basic_task_info.docker_project_root
                ),
            ],
        )
        format_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "format",
                get_all_python_folders(
                    project_root=basic_task_info.docker_project_root
                ),
            ],
        )
        Format(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=sort_imports_args),
            call(args=format_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_ruff_fix_safe_requires(basic_task_info: BasicTaskInfo) -> None:
    assert Lint(basic_task_info=basic_task_info).required_tasks() == [
        Format(basic_task_info=basic_task_info),
        AllSubprojectUnitTests(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_ruff_fix_safe(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        fix_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--fix",
                get_all_non_test_folders(
                    project_root=basic_task_info.docker_project_root
                ),
            ],
        )
        fix_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D,FBT",
                "--fix",
                get_all_test_folders(project_root=basic_task_info.docker_project_root),
            ],
        )
        Lint(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=fix_src_args),
            call(args=fix_test_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_apply_ruff_fix_unsafe_requires(basic_task_info: BasicTaskInfo) -> None:
    assert LintApplyUnsafeFixes(basic_task_info=basic_task_info).required_tasks() == [
        Lint(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_apply_run_ruff_fix_unsafe(basic_task_info: BasicTaskInfo) -> None:
    with (
        patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock,
        patch(
            "build_support.ci_cd_tasks.lint_tasks.commit_changes_if_diff"
        ) as commit_changes_mock,
    ):
        fix_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--fix",
                "--unsafe-fixes",
                get_all_non_test_folders(
                    project_root=basic_task_info.docker_project_root
                ),
            ],
        )
        fix_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D,FBT",
                "--fix",
                "--unsafe-fixes",
                get_all_test_folders(project_root=basic_task_info.docker_project_root),
            ],
        )
        LintApplyUnsafeFixes(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=fix_src_args),
            call(args=fix_test_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)
        commit_changes_mock.assert_called_once_with(
            commit_message=(
                "Committing staged changes for before applying unsafe ruff fixes."
            ),
            project_root=basic_task_info.docker_project_root,
            local_uid=basic_task_info.local_uid,
            local_gid=basic_task_info.local_gid,
            local_user_env=basic_task_info.local_user_env,
        )
