from argparse import Namespace
from copy import deepcopy
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import get_local_info_yaml
from build_support.ci_cd_vars.project_structure import maybe_build_dir
from build_support.dump_ci_cd_run_info import parse_args, run_main


@pytest.fixture(params=[Path("usr/dev"), Path("user/dev")])
def docker_project_root_arg(request: SubRequest, tmp_path: Path) -> Path:
    return maybe_build_dir(dir_to_build=tmp_path.joinpath(request.param))


@pytest.fixture(params=[Path("path/to/project"), Path("some/other/path")])
def non_docker_project_root_arg(request: SubRequest, tmp_path: Path) -> Path:
    return maybe_build_dir(dir_to_build=tmp_path.joinpath(request.param))


@pytest.fixture(params=[True, False])
def ci_cd_integration_test_mode(request: SubRequest) -> bool:
    return request.param


@pytest.fixture()
def cli_arg_combo(
    non_docker_project_root_arg: Path,
    docker_project_root_arg: Path,
    basic_task_info: BasicTaskInfo,
    ci_cd_integration_test_mode: bool,
) -> BasicTaskInfo:
    return BasicTaskInfo(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        local_uid=basic_task_info.local_uid,
        local_gid=basic_task_info.local_gid,
        ci_cd_integration_test_mode=ci_cd_integration_test_mode,
        local_user_env=basic_task_info.local_user_env,
    )


@pytest.fixture()
def args_to_test_single_task(
    cli_arg_combo: BasicTaskInfo,
) -> list[str]:
    return [
        str(x)
        for x in [
            "--non-docker-project-root",
            cli_arg_combo.non_docker_project_root,
            "--docker-project-root",
            cli_arg_combo.docker_project_root,
            "--user-id",
            cli_arg_combo.local_uid,
            "--group-id",
            cli_arg_combo.local_gid,
        ]
        + (
            ["--ci-cd-integration-test-mode"]
            if cli_arg_combo.ci_cd_integration_test_mode
            else []
        )
    ]


@pytest.fixture()
def expected_namespace_single_task(
    cli_arg_combo: BasicTaskInfo,
) -> Namespace:
    return Namespace(
        non_docker_project_root=cli_arg_combo.non_docker_project_root,
        docker_project_root=cli_arg_combo.docker_project_root,
        user_id=cli_arg_combo.local_uid,
        group_id=cli_arg_combo.local_gid,
        ci_cd_integration_test_mode=cli_arg_combo.ci_cd_integration_test_mode,
    )


def test_parse_args_single_task(
    args_to_test_single_task: list[str],
    expected_namespace_single_task: Namespace,
) -> None:
    assert parse_args(args=args_to_test_single_task) == expected_namespace_single_task


def test_parse_args_no_group_id() -> None:
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
            ],
        )


def test_parse_args_no_user_id() -> None:
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
            ],
        )


def test_parse_args_no_docker_project_root() -> None:
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
            ],
        )


def test_parse_args_no_non_docker_project_root() -> None:
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
            ],
        )


def test_run_main_success(cli_arg_combo: BasicTaskInfo) -> None:
    args = Namespace(
        non_docker_project_root=cli_arg_combo.non_docker_project_root,
        docker_project_root=cli_arg_combo.docker_project_root,
        user_id=cli_arg_combo.local_uid,
        group_id=cli_arg_combo.local_gid,
        ci_cd_integration_test_mode=cli_arg_combo.ci_cd_integration_test_mode,
    )
    run_main(args)
    local_info_yaml = get_local_info_yaml(
        project_root=cli_arg_combo.docker_project_root
    )
    observed_run_info_yaml = BasicTaskInfo.from_yaml(local_info_yaml.read_text())
    expected_run_info_yaml = deepcopy(cli_arg_combo)
    if (
        observed_run_info_yaml.local_user_env is not None
        and expected_run_info_yaml.local_user_env is not None
    ):
        # PYTEST is doing some weird ENV variable setting
        observed_run_info_yaml.local_user_env = {
            k: v
            for k, v in observed_run_info_yaml.local_user_env.items()
            if not k.startswith("PYTEST")
        }
        expected_run_info_yaml.local_user_env = {
            k: v
            for k, v in expected_run_info_yaml.local_user_env.items()
            if not k.startswith("PYTEST")
        }
    assert observed_run_info_yaml == expected_run_info_yaml
