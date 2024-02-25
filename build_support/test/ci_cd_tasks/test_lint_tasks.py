from pathlib import Path
from unittest.mock import call, patch

from build_support.ci_cd_tasks.env_setup_tasks import BuildDevEnvironment
from build_support.ci_cd_tasks.lint_tasks import Autoflake, Lint
from build_support.ci_cd_tasks.test_tasks import TestBuildSupport, TestPypi
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import get_all_python_folders
from build_support.dag_engine import concatenate_args


def test_lint_requires(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    assert Lint(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    ).required_tasks() == [
        BuildDevEnvironment(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
    ]


def test_run_lint(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        isort_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "isort",
                get_all_python_folders(project_root=docker_project_root),
            ],
        )
        black_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "black",
                get_all_python_folders(project_root=docker_project_root),
            ],
        )
        Lint(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ).run()
        assert run_process_mock.call_count == 2
        run_process_mock.assert_has_calls(
            calls=[
                call(args=isort_args),
                call(args=black_args),
            ],
        )


def test_autoflake_requires(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    assert Autoflake(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    ).required_tasks() == [
        Lint(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
        TestPypi(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
        TestBuildSupport(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
    ]


def test_run_autoflake(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.lint_tasks.run_process") as run_process_mock:
        autoflake_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "autoflake",
                "--remove-all-unused-imports",
                "--remove-duplicate-keys",
                "--in-place",
                "--recursive",
                get_all_python_folders(project_root=docker_project_root),
            ],
        )
        Autoflake(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ).run()
        run_process_mock.assert_called_once_with(args=autoflake_args)
