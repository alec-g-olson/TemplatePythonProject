"""A module for running tasks that are not domain specific."""
import json
from dataclasses import dataclass

from common_vars import (
    BASE_DOCKER_COMMAND,
    BRANCH,
    BUILD_DIR,
    DOCKER_COMMAND,
    DOCKER_CONTEXT,
    DOCKER_DEV_IMAGE,
    DOCKER_PROD_IMAGE,
    DOCKER_PULUMI_IMAGE,
    DOCKER_REMOTE_ALL_PYTHON_FOLDERS,
    DOCKER_REMOTE_ALL_SRC_FOLDERS,
    DOCKER_REMOTE_ALL_TEST_FOLDERS,
    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
    DOCKER_REMOTE_PYPI_SRC_AND_TEST,
    DOCKERFILE,
    GIT_DATA_FILE,
    INTERACTIVE_DOCKER_COMMAND,
    INTERACTIVE_PROD_DOCKER_COMMAND,
    INTERACTIVE_PULUMI_DOCKER_COMMAND,
    PROJECT_SETTINGS_TOML,
    PUSH_ALLOWED,
    PYPROJECT_TOML,
    PYTHON_PATH_TO_INCLUDE,
    THREADS_AVAILABLE,
    USER,
    VERSION,
)
from dag_engine import (
    TaskNode,
    concatenate_args,
    get_output_of_process,
    run_piped_processes,
    run_process,
)


class DockerLogin(TaskNode):
    """Logs into docker before trying to execute commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(self) -> None:
        """Runs docker login."""
        run_process(args=["docker", "login"])


class BuildDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return [DockerLogin()]

    def run(self) -> None:
        """Builds a stable environment for running dev commands."""
        run_process(
            args=[
                "docker",
                "build",
                "-f",
                DOCKERFILE,
                "--target",
                "dev",
                "--build-arg",
                "BUILDKIT_INLINE_CACHE=1",
                "-t",
                DOCKER_DEV_IMAGE,
                DOCKER_CONTEXT,
            ]
        )


class OpenDevDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the dev environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a dev docker image first."""
        return [BuildDevEnvironment()]

    def run(self) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(args=[INTERACTIVE_DOCKER_COMMAND, "/bin/bash"])
        )


class BuildProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return [DockerLogin()]

    def run(self) -> None:
        """Builds a stable environment for running prod commands."""
        run_process(
            args=[
                "docker",
                "build",
                "-f",
                DOCKERFILE,
                "--target",
                "prod",
                "--build-arg",
                "BUILDKIT_INLINE_CACHE=1",
                "-t",
                DOCKER_PROD_IMAGE,
                DOCKER_CONTEXT,
            ]
        )


class OpenProdDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the prod environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a prod docker image first."""
        return [BuildProdEnvironment()]

    def run(self) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(args=[INTERACTIVE_PROD_DOCKER_COMMAND, "/bin/bash"])
        )


class BuildPulumiEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running pulumi commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return [DockerLogin()]

    def run(self) -> None:
        """Builds a stable environment for running pulumi commands."""
        run_process(
            args=[
                "docker",
                "build",
                "-f",
                DOCKERFILE,
                "--target",
                "pulumi",
                "--build-arg",
                "BUILDKIT_INLINE_CACHE=1",
                "-t",
                DOCKER_PULUMI_IMAGE,
                DOCKER_CONTEXT,
            ]
        )


class OpenPulumiDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the pulumi environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a pulumi docker image first."""
        return [BuildPulumiEnvironment()]

    def run(self) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(args=[INTERACTIVE_PULUMI_DOCKER_COMMAND, "/bin/bash"])
        )


class Clean(TaskNode):
    """Removes all temporary files for a clean build environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(self) -> None:
        """Deletes all the temporary build files."""
        run_process(args=["rm", "-rf", BUILD_DIR])


class DockerPruneAll(TaskNode):
    """Clears all docker information for a clean docker environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(self) -> None:
        """Stops all docker processes and then clears all cached docker info."""
        run_piped_processes(
            processes=[["docker", "ps", "-q"], ["xargs", "-r", "docker", "stop"]]
        )
        run_process(args=["docker", "system", "prune", "--all", "--force"])


@dataclass
class GitInfo:
    """An object containing the current git information."""

    branch: str
    tags: list[str]

    @classmethod
    def from_json(cls, json_str: str) -> "GitInfo":
        """Builds an object from a json str."""
        json_vals = json.loads(json_str)
        return GitInfo(**json_vals)

    def to_json(self) -> str:
        """Dumps object as a json str."""
        return json.dumps(self.__dict__, indent=2)


class GetGitInfo(TaskNode):
    """Gets all git info we could need for checks during building."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(self) -> None:
        """Builds a json with required git info."""
        GIT_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        GIT_DATA_FILE.write_text(
            GitInfo(
                branch=BRANCH, tags=get_output_of_process(["git", "tag"]).split("\n")
            ).to_json()
        )


class TestBuildSanity(TaskNode):
    """Runs tests to ensure the following.

    - Branch and version are coherent.
    - Readme hasn't been wildly reformatted unexpectedly.
    """

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running tests."""
        return [GetGitInfo(), BuildDevEnvironment()]

    def run(self) -> None:
        """Runs tests in the build_test folder."""
        run_process(
            args=concatenate_args(
                args=[
                    DOCKER_COMMAND,
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
                ]
            )
        )


class TestPythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running style checks."""
        # Todo: Add in pulumi environment and test once pulumi build doesn't break
        return [BuildDevEnvironment()]  # , BuildPulumiEnvironment()]

    def run(self) -> None:
        """Runs all stylistic checks on code."""
        run_process(
            args=concatenate_args(
                args=[
                    DOCKER_COMMAND,
                    "isort",
                    "--check-only",
                    DOCKER_REMOTE_ALL_PYTHON_FOLDERS,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    DOCKER_COMMAND,
                    "black",
                    "--check",
                    DOCKER_REMOTE_ALL_PYTHON_FOLDERS,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[DOCKER_COMMAND, "pydocstyle", DOCKER_REMOTE_ALL_SRC_FOLDERS]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    DOCKER_COMMAND,
                    "pydocstyle",
                    "--add-ignore=D100,D104",
                    DOCKER_REMOTE_ALL_TEST_FOLDERS,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[DOCKER_COMMAND, "flake8", DOCKER_REMOTE_ALL_PYTHON_FOLDERS]
            )
        )
        mypy_command = concatenate_args(
            args=[
                BASE_DOCKER_COMMAND,
                "-e",
                "MYPYPATH=" + PYTHON_PATH_TO_INCLUDE,
                "--user",
                USER,
                DOCKER_DEV_IMAGE,
                "mypy",
                "--explicit-package-bases",
            ]
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    DOCKER_REMOTE_PYPI_SRC_AND_TEST,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
                ]
            )
        )
        # Todo: Uncomment once pulumi is working
        """
        run_process(
            args=concatenate_args(
                args=[
                    BASE_DOCKER_COMMAND,
                    "-e",
                    "MYPYPATH=" + PYTHON_PATH_TO_INCLUDE,
                    "--user",
                    USER,
                    DOCKER_PULUMI_IMAGE,
                    "mypy",
                    "--explicit-package-bases",
                    DOCKER_REMOTE_PULUMI,
                ]
            )
        )"""


class Lint(TaskNode):
    """Linting task."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure dev environment has been built before linting."""
        return [BuildDevEnvironment()]

    def run(self) -> None:
        """Lints all python files in project."""
        run_process(
            args=concatenate_args(
                args=[DOCKER_COMMAND, "isort", DOCKER_REMOTE_ALL_PYTHON_FOLDERS]
            )
        )
        run_process(
            args=concatenate_args(
                args=[DOCKER_COMMAND, "black", DOCKER_REMOTE_ALL_PYTHON_FOLDERS]
            )
        )


class PushTags(TaskNode):
    """Pushes tags to git, reserving the commit for a specific artifact push."""

    def required_tasks(self) -> list[TaskNode]:
        """Checks to see if the version is appropriate for the branch we are on."""
        return [TestBuildSanity()]

    def run(self) -> None:
        """Push tags."""
        if PUSH_ALLOWED:
            run_process(args=concatenate_args(args=["git", "tag", VERSION]))
            run_process(args=concatenate_args(args=["git", "push", "tags"]))
        else:
            exit(1)


@dataclass
class ProjectSettings:
    """An object containing the project settings for this project."""

    name: str

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectSettings":
        """Builds an object from a json str."""
        json_vals = json.loads(json_str)
        return ProjectSettings(**json_vals)

    def to_json(self) -> str:
        """Dumps object as a json str."""
        return json.dumps(self.__dict__, indent=2)


class MakeProjectFromTemplate(TaskNode):
    """Updates project based on the project settings yaml."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return [Clean()]

    def run(self) -> None:
        """Modifies the appropriate files to start a new project."""
        master_project_settings = ProjectSettings.from_json(
            PROJECT_SETTINGS_TOML.read_text()
        )
        new_text = ""
        for line in PYPROJECT_TOML.open():
            if line == 'name = "template_python_project"\n':
                new_text += f'name = "{master_project_settings.name}"\n'
            elif line.startswith("version = "):
                new_text += 'version = "0.0.0"\n'
            else:
                new_text += line
        PYPROJECT_TOML.write_text(new_text)
