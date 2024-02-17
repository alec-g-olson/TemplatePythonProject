from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from build_support.ci_cd_tasks.build_tasks import BuildAll, BuildDocs, BuildPypi
from build_support.ci_cd_tasks.env_setup_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    BuildPulumiEnvironment,
    Clean,
)
from build_support.ci_cd_tasks.lint_tasks import Autoflake, Lint
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi
from build_support.ci_cd_tasks.test_tasks import (
    TestAll,
    TestBuildSanity,
    TestPypi,
    TestPythonStyle,
)
from build_support.dag_engine import concatenate_args
from build_support.execute_build_steps import (
    CLI_ARG_TO_TASK,
    fix_permissions,
    parse_args,
    run_main,
)
from build_support.new_project_setup.setup_new_project import MakeProjectFromTemplate


def test_constants_not_changed_by_accident():
    assert CLI_ARG_TO_TASK == {
        "make_new_project": MakeProjectFromTemplate(),
        "clean": Clean(),
        "build_dev": BuildDevEnvironment(),
        "build_prod": BuildProdEnvironment(),
        "build_pulumi": BuildPulumiEnvironment(),
        "test_style": TestPythonStyle(),
        "test_build_sanity": TestBuildSanity(),
        "test_pypi": TestPypi(),
        "test": TestAll(),
        "lint": Lint(),
        "autoflake": Autoflake(),
        "build_pypi": BuildPypi(),
        "build_docs": BuildDocs(),
        "build": BuildAll(),
        "push_pypi": PushPypi(),
        "push": PushAll(),
    }


def test_fix_permissions(real_project_root_dir: Path):
    with patch("build_support.execute_build_steps.run_process") as run_process_mock:
        local_user = "1337:42"
        fix_permissions_args = concatenate_args(
            args=[
                "chown",
                "-R",
                local_user,
                [
                    path.absolute()
                    for path in real_project_root_dir.glob("*")
                    if path.name != ".git"
                ],
            ]
        )
        fix_permissions(local_user_uid=1337, local_user_gid=42)
        run_process_mock.assert_called_once_with(args=fix_permissions_args, silent=True)


@pytest.fixture(params=[Path("/usr/dev"), Path("/user/dev")])
def docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=[Path("/path/to/project"), Path("/some/other/path")])
def non_docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=CLI_ARG_TO_TASK.keys())
def build_task(request) -> str:
    return request.param


@pytest.fixture
def args_to_test_single_task(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_uid: int,
    local_gid: int,
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
            local_uid,
            "--group-id",
            local_gid,
            build_task,
        ]
    ]


@pytest.fixture
def expected_namespace_single_task(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_uid: int,
    local_gid: int,
    build_task: str,
) -> Namespace:
    return Namespace(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        user_id=local_uid,
        group_id=local_gid,
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
    local_uid: int,
    local_gid: int,
) -> list[str]:
    return [
        str(x)
        for x in [
            "--non-docker-project-root",
            non_docker_project_root_arg,
            "--docker-project-root",
            docker_project_root_arg,
            "--user-id",
            local_uid,
            "--group-id",
            local_gid,
        ]
    ] + list(CLI_ARG_TO_TASK.keys())


@pytest.fixture
def expected_namespace_all_tasks(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    local_uid: int,
    local_gid: int,
) -> Namespace:
    return Namespace(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        user_id=local_uid,
        group_id=local_gid,
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
                "INVALID_TASK_NAME",
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
                "clean",
            ]
        )


def test_run_main_success(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        user_id=local_uid,
        group_id=local_gid,
        build_tasks=["clean"],
    )
    with patch("build_support.execute_build_steps.run_tasks") as mock_run_tasks, patch(
        "build_support.execute_build_steps.fix_permissions"
    ) as mock_fix_permissions:
        run_main(args)
        mock_run_tasks.assert_called_once_with(
            tasks=[Clean()],
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        mock_fix_permissions.assert_called_once_with(
            local_user_uid=local_uid, local_user_gid=local_gid
        )


def test_run_main_exception(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    all_task_list = list(CLI_ARG_TO_TASK.keys())
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        user_id=local_uid,
        group_id=local_gid,
        build_tasks=all_task_list,
    )
    with patch("build_support.execute_build_steps.run_tasks") as mock_run_tasks, patch(
        "builtins.print"
    ) as mock_print, patch(
        "build_support.execute_build_steps.fix_permissions"
    ) as mock_fix_permissions:
        error_to_raise = RuntimeError("error_message")
        mock_run_tasks.side_effect = error_to_raise
        run_main(args)
        mock_run_tasks.assert_called_once_with(
            tasks=[CLI_ARG_TO_TASK[arg] for arg in all_task_list],
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        mock_print.assert_called_once_with(error_to_raise)
        mock_fix_permissions.assert_called_once_with(
            local_user_uid=local_uid, local_user_gid=local_gid
        )
