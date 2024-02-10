from pathlib import Path
from unittest.mock import call, patch

from build_tasks.env_setup_tasks import BuildDevEnvironment
from build_tasks.lint_tasks import Autoflake, Lint
from build_tasks.test_tasks import TestBuildSanity, TestPypi
from build_vars.docker_vars import DockerTarget, get_docker_command_for_image
from build_vars.file_and_dir_path_vars import get_all_python_folders
from dag_engine import concatenate_args


def test_lint_requires():
    assert Lint().required_tasks() == [BuildDevEnvironment()]


def test_run_lint(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.lint_tasks.run_process") as run_process_mock:
        isort_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "isort",
                get_all_python_folders(project_root=docker_project_root),
            ]
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
            ]
        )
        Lint().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 2
        run_process_mock.assert_has_calls(
            calls=[
                call(args=isort_args),
                call(args=black_args),
            ]
        )


def test_autoflake_requires():
    assert Autoflake().required_tasks() == [Lint(), TestPypi(), TestBuildSanity()]


def test_run_autoflake(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.lint_tasks.run_process") as run_process_mock:
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
            ]
        )
        Autoflake().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(args=autoflake_args)
