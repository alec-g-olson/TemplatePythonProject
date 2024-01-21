"""The entry point into running build tools."""
import sys

from build_tasks.combined_tasks import Autoflake, Push, Test
from build_tasks.common_build_tasks import (
    Clean,
    DockerPruneAll,
    GetGitInfo,
    Lint,
    MakeProjectFromTemplate,
    OpenDevDockerShell,
    OpenProdDockerShell,
    OpenPulumiDockerShell,
    TestBuildSanity,
)
from build_tasks.python_build_tasks import BuildPypi, PushPypi, TestPypi
from dag_engine import TaskNode, run_tasks

if __name__ == "__main__":
    cli_arg_to_task: dict[str, TaskNode] = {
        "make_new_project": MakeProjectFromTemplate(),
        "docker_prune_all": DockerPruneAll(),
        "clean": Clean(),
        "open_dev_docker_shell": OpenDevDockerShell(),
        "open_prod_docker_shell": OpenProdDockerShell(),
        "open_pulumi_docker_shell": OpenPulumiDockerShell(),
        "get_git_info": GetGitInfo(),
        "test_build_sanity": TestBuildSanity(),
        "test_without_style": TestPypi(),
        "test": Test(),
        "lint": Lint(),
        "autoflake": Autoflake(),
        "build_pypi": BuildPypi(),
        "push_pypi": PushPypi(),
        "push": Push(),
    }
    tasks = [cli_arg_to_task[arg] for arg in sys.argv[1:]]
    run_tasks(tasks=tasks)
