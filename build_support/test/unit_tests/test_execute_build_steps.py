from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.build_tasks import (
    BuildAll,
    BuildDocs,
    BuildPypi,
)
from build_support.ci_cd_tasks.env_setup_tasks import (
    Clean,
    SetupDevEnvironment,
    SetupInfraEnvironment,
    SetupProdEnvironment,
)
from build_support.ci_cd_tasks.lint_tasks import (
    ApplyRuffFixUnsafe,
    Lint,
    RuffFixSafe,
)
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi
from build_support.ci_cd_tasks.task_node import (
    BasicTaskInfo,
    PerSubprojectTask,
    TaskNode,
)
from build_support.ci_cd_tasks.validation_tasks import (
    SubprojectUnitTests,
    ValidateAll,
    ValidatePythonStyle,
)
from build_support.ci_cd_vars.subproject_structure import SubprojectContext
from build_support.execute_build_steps import (
    CLI_ARG_TO_TASK,
    CliTaskInfo,
    fix_permissions,
    parse_args,
    run_main,
)
from build_support.new_project_setup.setup_new_project import MakeProjectFromTemplate
from build_support.process_runner import ProcessVerbosity, concatenate_args


def test_constants_not_changed_by_accident() -> None:
    assert CLI_ARG_TO_TASK.copy() == {
        "make_new_project": CliTaskInfo(task_node=MakeProjectFromTemplate),
        "clean": CliTaskInfo(task_node=Clean),
        "setup_dev_env": CliTaskInfo(task_node=SetupDevEnvironment),
        "setup_prod_env": CliTaskInfo(task_node=SetupProdEnvironment),
        "setup_infra_env": CliTaskInfo(task_node=SetupInfraEnvironment),
        "test_style": CliTaskInfo(task_node=ValidatePythonStyle),
        "test_build_support": CliTaskInfo(
            task_node=SubprojectUnitTests,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        ),
        "test_pypi": CliTaskInfo(
            task_node=SubprojectUnitTests, subproject_context=SubprojectContext.PYPI
        ),
        "test": CliTaskInfo(task_node=ValidateAll),
        "lint": CliTaskInfo(task_node=Lint),
        "ruff_fix_safe": CliTaskInfo(task_node=RuffFixSafe),
        "apply_unsafe_ruff_fixes": CliTaskInfo(task_node=ApplyRuffFixUnsafe),
        "build_pypi": CliTaskInfo(task_node=BuildPypi),
        "build_docs": CliTaskInfo(task_node=BuildDocs),
        "build": CliTaskInfo(task_node=BuildAll),
        "push_pypi": CliTaskInfo(task_node=PushPypi),
        "push": CliTaskInfo(task_node=PushAll),
    }


def test_fix_permissions(real_project_root_dir: Path) -> None:
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
            ],
        )
        fix_permissions(local_user_uid=1337, local_user_gid=42)
        run_process_mock.assert_called_once_with(
            args=fix_permissions_args, verbosity=ProcessVerbosity.SILENT
        )


@pytest.fixture(params=[Path("/usr/dev"), Path("/user/dev")])
def docker_project_root_arg(request: SubRequest) -> Path:
    return request.param


@pytest.fixture(params=[Path("/path/to/project"), Path("/some/other/path")])
def non_docker_project_root_arg(request: SubRequest) -> Path:
    return request.param


@pytest.fixture(params=CLI_ARG_TO_TASK.keys())
def build_task(request: SubRequest) -> str:
    return request.param


@pytest.fixture()
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


@pytest.fixture()
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
    args_to_test_single_task: list[str],
    expected_namespace_single_task: Namespace,
) -> None:
    assert parse_args(args=args_to_test_single_task) == expected_namespace_single_task


@pytest.fixture()
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


@pytest.fixture()
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


def test_parse_args_all_task(
    args_to_test_all_tasks: list[str], expected_namespace_all_tasks: Namespace
) -> None:
    assert parse_args(args=args_to_test_all_tasks) == expected_namespace_all_tasks


def test_parse_args_no_task() -> None:
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
            ],
        )


def test_parse_args_bad_task() -> None:
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
            ],
        )


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


def test_run_main_success(basic_task_info: BasicTaskInfo) -> None:
    args = Namespace(
        non_docker_project_root=basic_task_info.non_docker_project_root,
        docker_project_root=basic_task_info.docker_project_root,
        user_id=basic_task_info.local_uid,
        group_id=basic_task_info.local_gid,
        build_tasks=["clean"],
    )
    with (
        patch("build_support.execute_build_steps.run_tasks") as mock_run_tasks,
        patch(
            "build_support.execute_build_steps.fix_permissions",
        ) as mock_fix_permissions,
    ):
        run_main(args)
        mock_run_tasks.assert_called_once_with(
            tasks=[
                Clean(
                    basic_task_info=BasicTaskInfo(
                        non_docker_project_root=basic_task_info.non_docker_project_root,
                        docker_project_root=basic_task_info.docker_project_root,
                        local_uid=basic_task_info.local_uid,
                        local_gid=basic_task_info.local_gid,
                        local_user_env=basic_task_info.local_user_env,
                    )
                )
            ],
        )
        mock_fix_permissions.assert_called_once_with(
            local_user_uid=basic_task_info.local_uid,
            local_user_gid=basic_task_info.local_gid,
        )


def test_run_main_bad_cli_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        user_id=local_uid,
        group_id=local_gid,
        build_tasks=["clean"],
    )
    with (
        patch(
            "build_support.execute_build_steps.CLI_ARG_TO_TASK",
            {
                "clean": CliTaskInfo(
                    task_node=Clean, subproject_context=SubprojectContext.PYPI
                )
            },
        ),
    ):
        msg = (
            "Incoherent CLI Task Info.\n"
            "\ttask_node: Clean\n"
            "\tsubproject_context: PYPI"
        )
        with pytest.raises(ValueError, match=msg):
            run_main(args)


def test_run_main_exception(basic_task_info: BasicTaskInfo) -> None:
    all_task_list = list(CLI_ARG_TO_TASK.keys())
    args = Namespace(
        non_docker_project_root=basic_task_info.non_docker_project_root,
        docker_project_root=basic_task_info.docker_project_root,
        user_id=basic_task_info.local_uid,
        group_id=basic_task_info.local_gid,
        build_tasks=all_task_list,
    )
    with (
        patch("build_support.execute_build_steps.run_tasks") as mock_run_tasks,
        patch(
            "builtins.print",
        ) as mock_print,
        patch(
            "build_support.execute_build_steps.fix_permissions",
        ) as mock_fix_permissions,
    ):
        error_to_raise = RuntimeError("error_message")
        mock_run_tasks.side_effect = error_to_raise
        run_main(args)
        requested_tasks = [
            CLI_ARG_TO_TASK[arg].get_task_node(basic_task_info=basic_task_info)
            for arg in args.build_tasks
        ]
        mock_run_tasks.assert_called_once_with(tasks=requested_tasks)
        mock_print.assert_called_once_with(error_to_raise)
        mock_fix_permissions.assert_called_once_with(
            local_user_uid=basic_task_info.local_uid,
            local_user_gid=basic_task_info.local_gid,
        )


def test_get_standard_task_node(basic_task_info: BasicTaskInfo) -> None:
    class TestTaskNode(TaskNode):
        def required_tasks(self) -> list[TaskNode]:
            return []  # pragma: no cover - never called, just a test class

        def run(self) -> None:
            """Does nothing.  Pycharm doesn't like 'pass' for some reason."""

    cli_task_info = CliTaskInfo(task_node=TestTaskNode)
    assert cli_task_info.get_task_node(basic_task_info=basic_task_info) == TestTaskNode(
        basic_task_info=basic_task_info
    )


def test_get_subproject_specific_task_node(basic_task_info: BasicTaskInfo) -> None:
    class TestSubprojectSpecificTaskNode(PerSubprojectTask):
        def required_tasks(self) -> list[TaskNode]:
            return []  # pragma: no cover - never called, just a test class

        def run(self) -> None:
            """Does nothing.  Pycharm doesn't like 'pass' for some reason."""

    cli_task_info = CliTaskInfo(
        task_node=TestSubprojectSpecificTaskNode,
        subproject_context=SubprojectContext.PYPI,
    )
    assert cli_task_info.get_task_node(
        basic_task_info=basic_task_info
    ) == TestSubprojectSpecificTaskNode(
        basic_task_info=basic_task_info,
        subproject_context=SubprojectContext.PYPI,
    )
