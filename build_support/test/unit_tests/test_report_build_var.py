from argparse import Namespace
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_interactive_docker_command_for_image,
)
from build_support.ci_cd_vars.project_structure import maybe_build_dir
from build_support.report_build_var import AllowedCliArgs, parse_args, run_main


def test_allowed_cli_ars_not_changed_by_accident() -> None:
    assert {arg: arg.value for arg in AllowedCliArgs} == {
        AllowedCliArgs.DEV_DOCKER_INTERACTIVE: "interactive-dev-docker-command",
        AllowedCliArgs.PROD_DOCKER_INTERACTIVE: "interactive-prod-docker-command",
        AllowedCliArgs.INFRA_DOCKER_INTERACTIVE: "interactive-infra-docker-command",
    }


@pytest.fixture(params=[Path("usr/dev"), Path("user/dev")])
def docker_project_root_arg(request: SubRequest, tmp_path: Path) -> Path:
    return maybe_build_dir(dir_to_build=tmp_path.joinpath(request.param))


@pytest.fixture(params=[Path("path/to/project"), Path("some/other/path")])
def non_docker_project_root_arg(request: SubRequest, tmp_path: Path) -> Path:
    return maybe_build_dir(dir_to_build=tmp_path.joinpath(request.param))


@pytest.fixture(params=[arg.value for arg in AllowedCliArgs])
def build_variable_to_report(request: SubRequest) -> str:
    return cast(str, request.param)


@pytest.fixture
def args_to_test_single_var(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    build_variable_to_report: str,
) -> list[str]:
    return [
        str(x)
        for x in [
            "--non-docker-project-root",
            non_docker_project_root_arg,
            "--docker-project-root",
            docker_project_root_arg,
            "--build-variable-to-report",
            build_variable_to_report,
        ]
    ]


@pytest.fixture
def expected_namespace_single_var(
    docker_project_root_arg: Path,
    non_docker_project_root_arg: Path,
    build_variable_to_report: str,
) -> Namespace:
    return Namespace(
        non_docker_project_root=non_docker_project_root_arg,
        docker_project_root=docker_project_root_arg,
        build_variable_to_report=build_variable_to_report,
    )


def test_parse_args_single_var(
    args_to_test_single_var: list[str], expected_namespace_single_var: Namespace
) -> None:
    assert parse_args(args=args_to_test_single_var) == expected_namespace_single_var


def test_parse_args_no_task() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
            ]
        )


def test_parse_args_bad_var() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
                "--build-variable-to-report",
                "INVALID_VARIABLE_NAME",
            ]
        )


def test_parse_args_no_docker_project_root() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--build-variable-to-report",
                "get-interactive-dev-docker-command",
            ]
        )


def test_parse_args_no_non_docker_project_root() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--docker-project-root",
                "docker_project_root",
                "--build-variable-to-report",
                "get-interactive-dev-docker-command",
            ]
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_main_for_each_var_in_enum(
    mock_project_root: Path, docker_project_root: Path
) -> None:
    for var_to_report in AllowedCliArgs:
        args = Namespace(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            build_variable_to_report=var_to_report,
        )
        run_main(args)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_main_for_get_interactive_dev(
    mock_project_root: Path, docker_project_root: Path
) -> None:
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        build_variable_to_report=AllowedCliArgs.DEV_DOCKER_INTERACTIVE,
    )
    with patch("builtins.print") as mock_print:
        run_main(args)
        mock_print.assert_called_once_with(
            " ".join(
                get_interactive_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                )
            )
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_main_for_get_interactive_prod(
    mock_project_root: Path, docker_project_root: Path
) -> None:
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        build_variable_to_report=AllowedCliArgs.PROD_DOCKER_INTERACTIVE,
    )
    with patch("builtins.print") as mock_print:
        run_main(args)
        mock_print.assert_called_once_with(
            " ".join(
                get_interactive_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.PROD,
                )
            )
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_main_for_get_interactive_infra(
    mock_project_root: Path, docker_project_root: Path
) -> None:
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        build_variable_to_report=AllowedCliArgs.INFRA_DOCKER_INTERACTIVE,
    )
    with patch("builtins.print") as mock_print:
        run_main(args)
        mock_print.assert_called_once_with(
            " ".join(
                get_interactive_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.INFRA,
                )
            )
        )
