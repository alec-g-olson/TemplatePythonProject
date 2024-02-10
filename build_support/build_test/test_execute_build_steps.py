from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from build_tasks.build_tasks import BuildPypi
from build_tasks.env_setup_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    BuildPulumiEnvironment,
    Clean,
    GetGitInfo,
)
from build_tasks.lint_tasks import Autoflake, Lint
from build_tasks.push_tasks import PushAll, PushPypi
from build_tasks.test_tasks import TestAll, TestBuildSanity, TestPypi, TestPythonStyle
from dag_engine import concatenate_args
from execute_build_steps import CLI_ARG_TO_TASK, fix_permissions, parse_args, run_main
from new_project_setup.setup_new_project import MakeProjectFromTemplate


def test_constants_not_changed_by_accident():
    assert CLI_ARG_TO_TASK == {
        "make_new_project": MakeProjectFromTemplate(),
        "clean": Clean(),
        "build_dev": BuildDevEnvironment(),
        "build_prod": BuildProdEnvironment(),
        "build_pulumi": BuildPulumiEnvironment(),
        "get_git_info": GetGitInfo(),
        "test_style": TestPythonStyle(),
        "test_build_sanity": TestBuildSanity(),
        "test_pypi": TestPypi(),
        "test": TestAll(),
        "lint": Lint(),
        "autoflake": Autoflake(),
        "build_pypi": BuildPypi(),
        "push_pypi": PushPypi(),
        "push": PushAll(),
    }


def test_fix_permissions():
    with patch("execute_build_steps.run_process") as run_process_mock:
        local_user = "local_user"
        args = [
            "chown",
            "-R",
            local_user,
            [
                path.absolute()
                for path in Path(__file__).parent.parent.parent.glob("*")
                if path.name != ".git"
            ],
        ]
        fix_permissions(local_user=local_user)
        run_process_mock.assert_called_once_with(
            args=concatenate_args(args=args), silent=True
        )


@pytest.fixture(params=[Path("/usr/dev"), Path("/user/dev")])
def docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=[Path("/path/to/project"), Path("/some/other/path")])
def non_docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=["20", "500"])
def user_id(request) -> str:
    return request.param


@pytest.fixture(params=["1", "1337"])
def group_id(request) -> str:
    return request.param


@pytest.fixture(params=CLI_ARG_TO_TASK.keys())
def build_task(request) -> str:
    return request.param


@pytest.fixture
def args_to_test_single_task(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_username: str,
    user_id: str,
    group_id: str,
    build_task: str,
) -> list[str]:
    return [
        str(x)
        for x in [
            "--non-docker-project-root",
            non_docker_project_root_arg,
            "--docker-project-root",
            docker_project_root_arg,
            "--user-id",
            user_id,
            "--group-id",
            group_id,
            "--local-username",
            local_username,
            build_task,
        ]
    ]


@pytest.fixture
def expected_namespace_single_task(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_username: str,
    user_id: str,
    group_id: str,
    build_task: str,
) -> Namespace:
    return Namespace(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        local_username=local_username,
        user_id=user_id,
        group_id=group_id,
        build_tasks=[build_task],
    )


def test_parse_args_single_task(
    args_to_test_single_task, expected_namespace_single_task
):
    assert parse_args(args=args_to_test_single_task) == expected_namespace_single_task


@pytest.fixture
def args_to_test_all_tasks(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_username: str,
    user_id: str,
    group_id: str,
) -> list[str]:
    return [
        str(x)
        for x in [
            "--non-docker-project-root",
            non_docker_project_root_arg,
            "--docker-project-root",
            docker_project_root_arg,
            "--user-id",
            user_id,
            "--group-id",
            group_id,
            "--local-username",
            local_username,
        ]
    ] + list(CLI_ARG_TO_TASK.keys())


@pytest.fixture
def expected_namespace_all_tasks(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_username: str,
    user_id: str,
    group_id: str,
) -> Namespace:
    return Namespace(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        local_username=local_username,
        user_id=user_id,
        group_id=group_id,
        build_tasks=list(CLI_ARG_TO_TASK.keys()),
    )


def test_parse_args_all_task(args_to_test_all_tasks, expected_namespace_all_tasks):
    assert parse_args(args=args_to_test_all_tasks) == expected_namespace_all_tasks


def test_parse_args_no_task():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--user-id",
                "20",
                "--group-id",
                "101",
                "--local-username",
                "local_username",
            ]
        )


def test_parse_args_bad_task():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--user-id",
                "20",
                "--group-id",
                "101",
                "--local-username",
                "local_username",
                "INVALID_TASK_NAME",
            ]
        )


def test_parse_args_no_username():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--user-id",
                "20",
                "--group-id",
                "101",
                "clean",
            ]
        )


def test_parse_args_no_group_id():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--user-id",
                "20",
                "--local-username",
                "local_username",
                "clean",
            ]
        )


def test_parse_args_no_user_id():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--group-id",
                "101",
                "--local-username",
                "local_username",
                "clean",
            ]
        )


def test_parse_args_no_docker_project_root():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--user-id",
                "20",
                "--group-id",
                "101",
                "--local-username",
                "local_username",
                "clean",
            ]
        )


def test_parse_args_no_non_docker_project_root():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--docker-project-root",
                "docker_project_root",
                "--user-id",
                "20",
                "--group-id",
                "101",
                "--local-username",
                "local_username",
                "clean",
            ]
        )


def test_run_main_success(
    mock_project_root: Path,
    docker_project_root: Path,
    local_username: str,
    user_id: str,
    group_id: str,
):
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_username=local_username,
        user_id=user_id,
        group_id=group_id,
        build_tasks=["clean"],
    )
    with patch("execute_build_steps.run_tasks") as mock_run_tasks, patch(
        "execute_build_steps.fix_permissions"
    ) as mock_fix_permissions:
        run_main(args)
        mock_run_tasks.assert_called_once_with(
            tasks=[Clean()],
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_username=local_username,
        )
        mock_fix_permissions.assert_called_once_with(
            local_user=":".join([user_id, group_id])
        )


def test_run_main_exception(
    mock_project_root: Path,
    docker_project_root: Path,
    local_username: str,
    user_id: str,
    group_id: str,
):
    all_task_list = list(CLI_ARG_TO_TASK.keys())
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_username=local_username,
        user_id=user_id,
        group_id=group_id,
        build_tasks=all_task_list,
    )
    with patch("execute_build_steps.run_tasks") as mock_run_tasks, patch(
        "builtins.print"
    ) as mock_print, patch(
        "execute_build_steps.fix_permissions"
    ) as mock_fix_permissions:
        error_to_raise = RuntimeError("error_message")
        mock_run_tasks.side_effect = error_to_raise
        run_main(args)
        mock_run_tasks.assert_called_once_with(
            tasks=[CLI_ARG_TO_TASK[arg] for arg in all_task_list],
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_username=local_username,
        )
        mock_print.assert_called_once_with(error_to_raise)
        mock_fix_permissions.assert_called_once_with(
            local_user=":".join([user_id, group_id])
        )
