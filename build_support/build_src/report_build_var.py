"""The entry point into running build tools."""

from argparse import ArgumentParser
from enum import Enum
from pathlib import Path

from build_vars.docker_vars import (
    DockerTarget,
    get_interactive_docker_command_for_image,
)


class AllowedCliArgs(Enum):
    """An Enum to track the retrievable variables."""

    GET_INTERACTIVE_DEV_DOCKER_COMMAND = "get-interactive-dev-docker-command"
    GET_INTERACTIVE_PROD_DOCKER_COMMAND = "get-interactive-prod-docker-command"
    GET_INTERACTIVE_PULUMI_DOCKER_COMMAND = "get-interactive-pulumi-docker-command"


if __name__ == "__main__":
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
    args = parser.parse_args()
    non_docker_project_root = args.non_docker_project_root
    docker_project_root = args.docker_project_root
    command = AllowedCliArgs(args.build_variable_to_report)
    match command:
        case AllowedCliArgs.GET_INTERACTIVE_DEV_DOCKER_COMMAND:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.DEV,
            )
        case AllowedCliArgs.GET_INTERACTIVE_PROD_DOCKER_COMMAND:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.PROD,
            )
        case AllowedCliArgs.GET_INTERACTIVE_PULUMI_DOCKER_COMMAND:
            values = get_interactive_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=DockerTarget.PULUMI,
            )
        case _:
            raise ValueError(f"{repr(command)} is not a valid enum of AllowedCliArgs.")
    print(" ".join(values))
