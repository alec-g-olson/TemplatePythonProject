"""Module for tasks that rely on multiple domains.

We can also put collective tasks here.
e.g. A "Test" task that runs all domain specific tests.
"""

from pathlib import Path

from build_tasks.common_build_tasks import (
    Lint,
    PushTags,
    TestBuildSanity,
    TestPythonStyle,
)
from build_tasks.python_build_tasks import PushPypi, TestPypi
from common_vars import (
    DockerTarget,
    get_all_python_folders,
    get_docker_command_for_image,
)
from dag_engine import TaskNode, concatenate_args, run_process


class Push(TaskNode):
    """A collective push task used to push all elements of the project at once."""

    def required_tasks(self) -> list[TaskNode]:
        """Adds all required "sub-pushes" to the DAG."""
        return [PushTags(), PushPypi()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Does nothing."""


class Test(TaskNode):
    """A collective test task used to test all elements of the project."""

    def required_tasks(self) -> list[TaskNode]:
        """Adds all required "subtests" to the DAG."""
        return [TestPythonStyle(), TestPypi(), TestBuildSanity()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Does nothing."""


class Autoflake(TaskNode):
    """Task for running autoflake on all python files in project."""

    def required_tasks(self) -> list[TaskNode]:
        """Run required tasks, including domain specific tests.

        We must ensure that all domain specific tests are passing.
        Autoflake can cause cascading rewrites if some code has errors.
        """
        return [Lint(), TestPypi()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs autoflake on all python files."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--remove-duplicate-keys",
                    "--in-place",
                    "--recursive",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
