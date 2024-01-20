"""The entry point into running build tools."""
import argparse

from build_tasks.combined_tasks import Autoflake, Push, Test
from build_tasks.common_build_tasks import (
    Clean,
    DockerPruneAll,
    Lint,
    OpenDevDockerShell,
    OpenProdDockerShell,
    OpenPulumiDockerShell,
)
from build_tasks.python_build_tasks import BuildPypi, PushPypi, TestPypi
from dag_engine import TaskNode, run_task

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("taskToRun", type=str)
    args = parser.parse_args()
    task_name = args.taskToRun
    task: TaskNode
    match task_name:
        case "docker_prune_all":
            task = DockerPruneAll()
        case "clean":
            task = Clean()
        case "open_dev_docker_shell":
            task = OpenDevDockerShell()
        case "open_prod_docker_shell":
            task = OpenProdDockerShell()
        case "open_pulumi_docker_shell":
            task = OpenPulumiDockerShell()
        case "test_without_style":
            task = TestPypi()
        case "test":
            task = Test()
        case "lint":
            task = Lint()
        case "autoflake":
            task = Autoflake()
        case "build_pypi":
            task = BuildPypi()
        case "push_pypi":
            task = PushPypi()
        case "push":
            task = Push()
        case _:
            exit(1)
    run_task(task)
