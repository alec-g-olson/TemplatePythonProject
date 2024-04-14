"""Executable that dumps project level information for the CI/CD pipeline to use."""

from argparse import ArgumentParser, Namespace
from os import environ
from pathlib import Path
from pwd import getpwuid

from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_vars.file_and_dir_path_vars import get_local_info_yaml


def parse_args(args: list[str] | None = None) -> Namespace:
    """Parses arguments from list given or the command line.

    Args:
        args (list[str] | None): Args to parse.  Defaults to None, causing
            sys.argv[1:] to be used.

    Returns:
        Namespace: A namespace made from the parsed args.
    """
    parser = ArgumentParser(
        prog="ExecuteBuildSteps",
        description="This tool exists to facilitate building, testing, "
        "and deploying this project's artifacts",
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
    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="User ID, used to return files made by docker to owner.",
    )
    parser.add_argument(
        "--group-id",
        type=int,
        required=True,
        help="User's Group ID, used to return files made by docker to owner.",
    )
    parser.add_argument(
        "--ci-cd-integration-test-mode",
        action="store_true",
        help="Set to true when running CI/CD integration tests to avoid recursive "
        "testing.",
    )
    return parser.parse_args(args=args)


def run_main(args: Namespace) -> None:
    """Runs the logic for the execute_build_steps main.

    Args:
        args (Namespace): A namespace generated by an ArgumentParser.

    Returns:
        None
    """
    local_uid = args.user_id
    local_gid = args.group_id
    local_user_env = None
    if local_uid or local_gid:
        local_user_env = environ.copy()
        local_user_env["HOME"] = f"/home/{getpwuid(local_uid).pw_name}/"
    docker_project_root = args.docker_project_root
    non_docker_project_root = args.non_docker_project_root
    basic_task_info = BasicTaskInfo(
        non_docker_project_root=non_docker_project_root,
        docker_project_root=docker_project_root,
        local_uid=local_uid,
        local_gid=local_gid,
        local_user_env=local_user_env,
        ci_cd_integration_test_mode=args.ci_cd_integration_test_mode,
    )
    print(basic_task_info.to_yaml())
    local_info_yaml = get_local_info_yaml(project_root=docker_project_root)
    local_info_yaml.write_text(basic_task_info.to_yaml())


if __name__ == "__main__":  # pragma: no cover - main
    run_main(args=parse_args())
