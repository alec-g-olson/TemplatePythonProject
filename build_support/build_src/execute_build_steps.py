"""The entry point into running build tools."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

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
from dag_engine import TaskNode, concatenate_args, run_process, run_tasks
from new_project_setup.setup_new_project import MakeProjectFromTemplate

CLI_ARG_TO_TASK: dict[str, TaskNode] = {
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


def fix_permissions(local_user_uid: int, local_user_gid: int) -> None:
    """Resets all file ownership to the local user after running processes."""
    local_user = f"{local_user_uid}:{local_user_gid}"
    run_process(
        args=concatenate_args(
            args=[
                "chown",
                "-R",
                local_user,
                [
                    path.absolute()
                    for path in Path(__file__).parent.parent.parent.glob("*")
                    if path.name != ".git"
                ],
            ]
        ),
        silent=True,
    )


def parse_args(args: list[str] | None = None) -> Namespace:
    """Builds the argument parser for main method."""
    parser = ArgumentParser(
        prog="ExecuteBuildSteps",
        description="This tool exists to facilitate building, testing, "
        "and deploying this project's artifacts",
    )
    parser.add_argument(
        "build_tasks",
        type=str,
        nargs="+",
        help="Build tasks to run.",
        choices=CLI_ARG_TO_TASK.keys(),
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
    return parser.parse_args(args=args)


def run_main(args: Namespace) -> None:
    """Runs the logic for the execute_build_steps main."""
    non_docker_project_root = args.non_docker_project_root
    docker_project_root = args.docker_project_root
    tasks = [CLI_ARG_TO_TASK[arg] for arg in args.build_tasks]
    try:
        run_tasks(
            tasks=tasks,
            non_docker_project_root=non_docker_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=args.user_id,
            local_user_gid=args.group_id,
        )
    except Exception as e:
        print(e)
    finally:
        fix_permissions(local_user_uid=args.user_id, local_user_gid=args.group_id)


if __name__ == "__main__":  # pragma: no cover - main
    run_main(args=parse_args())
