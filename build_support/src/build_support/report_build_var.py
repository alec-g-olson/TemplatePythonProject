"""The entry point into running build tools."""

from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path

from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_interactive_docker_command_for_image,
)


class AllowedCliArgs(Enum):
    """An Enum to track the retrievable variables."""

    DEV_DOCKER_INTERACTIVE = "interactive-dev-docker-command"
    PROD_DOCKER_INTERACTIVE = "interactive-prod-docker-command"
    PULUMI_DOCKER_INTERACTIVE = "interactive-pulumi-docker-command"


def parse_args(args: list[str] | None = None) -> Namespace:
    """Builds the argument parser for main method."""
    parser = ArgumentParser(
        prog="ReportBuildVars",
        description="This tool exists to get variables used during building.",
    )
    parser.add_argument(
        "--build-variable-to-report",
        type=str,
        required=True,
        help="Build variable to report.",
        choices=[enum.value for enum in AllowedCliArgs],
    )
    parser.add_argument(
        "--non-docker-project-root",
        type=Path,
        required=True,
        help="Path to project root on local machine, used to mount project "
        "when launching docker containers.",
    )
    parser.add_argument(
        "--docker-project-root",
        type=Path,
        required=True,
        help="Path to project root on docker machines, used to mount project "
        "when launching docker containers.",
    )
    return parser.parse_args(args=args)


def run_main(args: Namespace) -> None:
    """Runs the logic for the report_build_var main."""
    non_docker_project_root = args.non_docker_project_root
    docker_project_root = args.docker_project_root
    command = AllowedCliArgs(args.build_variable_to_report)
    match command:
        case AllowedCliArgs.DEV_DOCKER_INTERACTIVE:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.DEV,
            )
        case AllowedCliArgs.PROD_DOCKER_INTERACTIVE:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.PROD,
            )
        case AllowedCliArgs.PULUMI_DOCKER_INTERACTIVE:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.PULUMI,
            )
        case _:  # pragma: no cover - can't hit if all enums are implemented
            raise ValueError(
                f"{repr(command)} is not a supported enum of AllowedCliArgs."
            )
    print(" ".join(values))


if __name__ == "__main__":  # pragma: no cover - main
    run_main(args=parse_args())