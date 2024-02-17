from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_interactive_docker_command_for_image,
)
from build_support.report_build_var import AllowedCliArgs, parse_args, run_main


def test_allowed_cli_ars_not_changed_by_accident():
    assert {arg: arg.value for arg in AllowedCliArgs} == {
        AllowedCliArgs.DEV_DOCKER_INTERACTIVE: "interactive-dev-docker-command",
        AllowedCliArgs.PROD_DOCKER_INTERACTIVE: "interactive-prod-docker-command",
        AllowedCliArgs.PULUMI_DOCKER_INTERACTIVE: "interactive-pulumi-docker-command",
    }


@pytest.fixture(params=[Path("/usr/dev"), Path("/user/dev")])
def docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=[Path("/path/to/project"), Path("/some/other/path")])
def non_docker_project_root_arg(request) -> Path:
    return request.param


@pytest.fixture(params=[arg.value for arg in AllowedCliArgs])
def build_variable_to_report(request) -> str:
    return request.param


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


def test_parse_args_single_var(args_to_test_single_var, expected_namespace_single_var):
    assert parse_args(args=args_to_test_single_var) == expected_namespace_single_var


def test_parse_args_no_task():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--docker-project-root",
                "docker_project_root",
            ]
        )


def test_parse_args_bad_var():
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


def test_parse_args_no_docker_project_root():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--non-docker-project-root",
                "non_docker_project_root",
                "--build-variable-to-report",
                "get-interactive-dev-docker-command",
            ]
        )


def test_parse_args_no_non_docker_project_root():
    with pytest.raises(SystemExit):
        parse_args(
            args=[
                "--docker-project-root",
                "docker_project_root",
                "--build-variable-to-report",
                "get-interactive-dev-docker-command",
            ]
        )


def test_run_main_for_each_var_in_enum(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
):
    for var_to_report in [arg for arg in AllowedCliArgs]:
        args = Namespace(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            build_variable_to_report=var_to_report,
        )
        run_main(args)


def test_run_main_for_get_interactive_dev(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
):
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


def test_run_main_for_get_interactive_prod(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
):
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


def test_run_main_for_get_interactive_pulumi(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
):
    args = Namespace(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        build_variable_to_report=AllowedCliArgs.PULUMI_DOCKER_INTERACTIVE,
    )
    with patch("builtins.print") as mock_print:
        run_main(args)
        mock_print.assert_called_once_with(
            " ".join(
                get_interactive_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.PULUMI,
                )
            )
        )
