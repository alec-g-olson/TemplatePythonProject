"""The entry point into running build tools."""

from argparse import ArgumentParser
from pathlib import Path

from build_tasks.combined_tasks import Autoflake, Push, Test
from build_tasks.common_build_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    BuildPulumiEnvironment,
    Clean,
    GetGitInfo,
    Lint,
    MakeProjectFromTemplate,
    TestBuildSanity,
    TestPythonStyle,
)
from build_tasks.python_build_tasks import BuildPypi, PushPypi, TestPypi
from dag_engine import TaskNode, concatenate_args, run_process, run_tasks

CLI_ARG_TO_TASK: dict[str, TaskNode] = {
    "make_new_project": MakeProjectFromTemplate(),
    "clean": Clean(),
    "build_dev": BuildDevEnvironment(),
    "build_prod": BuildProdEnvironment(),
    "build_pulumi": BuildPulumiEnvironment(),
    "get_git_info": GetGitInfo(),
    "test_style": TestPythonStyle(),
    "test_build_sanity": TestBuildSanity(),
    "test_without_style": TestPypi(),
    "test": Test(),
    "lint": Lint(),
    "autoflake": Autoflake(),
    "build_pypi": BuildPypi(),
    "push_pypi": PushPypi(),
    "push": Push(),
}


def fix_permissions(local_user: str) -> None:
    """Builds a stable environment for running prod commands."""
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


if __name__ == "__main__":
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
        type=str,
        required=True,
        help="User ID, used to return files made by docker to owner.",
    )
    parser.add_argument(
        "--group-id",
        type=str,
        required=True,
        help="User's Group ID, used to return files made by docker to owner.",
    )
    args = parser.parse_args()
    tasks = [CLI_ARG_TO_TASK[arg] for arg in args.build_tasks]
    try:
        run_tasks(
            tasks=tasks,
            non_docker_project_root=args.non_docker_project_root,
            docker_project_root=args.docker_project_root,
        )
    except Exception as e:
        print(e)
    finally:
        fix_permissions(local_user=":".join([args.user_id, args.group_id]))
