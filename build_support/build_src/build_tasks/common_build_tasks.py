"""A module for running tasks that are not domain specific."""

import json
from dataclasses import dataclass
from pathlib import Path

from common_vars import (
    BRANCH,
    THREADS_AVAILABLE,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
    get_base_docker_command,
    get_build_dir,
    get_build_src_dir,
    get_build_test_dir,
    get_dev_docker_command,
    get_docker_dev_image,
    get_dockerfile,
    get_git_info_json,
    get_interactive_dev_docker_command,
    get_interactive_prod_docker_command,
    get_interactive_pulumi_docker_command,
    get_mypy_path_env,
    get_project_settings_json,
    get_project_version,
    get_pypi_src_and_test,
    get_pyproject_toml,
)
from dag_engine import TaskNode, concatenate_args, get_output_of_process, run_process


def get_docker_build_command(target: str, project_root: Path) -> list[str]:
    """Creates docker build command."""
    return concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=project_root),
            "--target",
            target,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            "-t",
            get_docker_dev_image(project_root=project_root),
            project_root.absolute(),
        ]
    )


class BuildDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Builds a stable environment for running dev commands."""
        run_process(
            args=get_docker_build_command(
                target="dev", project_root=docker_project_root
            )
        )


class OpenDevDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the dev environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a dev docker image first."""
        return [BuildDevEnvironment()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(
                args=[
                    get_interactive_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "/bin/bash",
                ]
            )
        )


class BuildProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Builds a stable environment for running prod commands."""
        run_process(
            args=get_docker_build_command(
                target="prod", project_root=docker_project_root
            )
        )


class OpenProdDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the prod environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a prod docker image first."""
        return [BuildProdEnvironment()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(
                args=[
                    get_interactive_prod_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "/bin/bash",
                ]
            )
        )


class BuildPulumiEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running pulumi commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Builds a stable environment for running pulumi commands."""
        run_process(
            args=get_docker_build_command(
                target="pulumi", project_root=docker_project_root
            )
        )


class OpenPulumiDockerShell(TaskNode):
    """Opens a shell in a temporary docker container running the pulumi environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Requires we build a pulumi docker image first."""
        return [BuildPulumiEnvironment()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs an interactive docker command that opens a bash shell."""
        run_process(
            args=concatenate_args(
                args=[
                    get_interactive_pulumi_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "/bin/bash",
                ]
            )
        )


class Clean(TaskNode):
    """Removes all temporary files for a clean build environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Deletes all the temporary build files."""
        run_process(args=["rm", "-rf", get_build_dir(project_root=docker_project_root)])


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

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Builds a json with required git info."""
        get_git_info_json(project_root=docker_project_root).parent.mkdir(
            parents=True, exist_ok=True
        )
        get_git_info_json(project_root=docker_project_root).write_text(
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

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs tests in the build_test folder."""
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_build_test_dir(project_root=docker_project_root),
                ]
            )
        )


class TestPythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running style checks."""
        # Todo: Add in pulumi environment and test once pulumi build doesn't break
        return [BuildDevEnvironment()]  # , BuildPulumiEnvironment()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Runs all stylistic checks on code."""
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "isort",
                    "--check-only",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "black",
                    "--check",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "pydocstyle",
                    get_all_src_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "pydocstyle",
                    "--add-ignore=D100,D104",
                    get_all_test_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "flake8",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command(
                    non_docker_project_root=non_docker_project_root,
                    docker_project_root=docker_project_root,
                ),
                "-e",
                get_mypy_path_env(project_root=docker_project_root),
                get_docker_dev_image(project_root=docker_project_root),
                "mypy",
                "--explicit-package-bases",
            ]
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_pypi_src_and_test(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_build_src_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_build_test_dir(project_root=docker_project_root),
                ]
            )
        )
        # Todo: Uncomment once pulumi is working
        """
        run_process(
            args=concatenate_args(
                args=[
                    get_base_docker_command(
                        external_project_root=external_project_root,
                    ),
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

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Lints all python files in project."""
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "isort",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_dev_docker_command(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                    ),
                    "black",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )


class PushTags(TaskNode):
    """Pushes tags to git, reserving the commit for a specific artifact push."""

    def required_tasks(self) -> list[TaskNode]:
        """Checks to see if the version is appropriate for the branch we are on."""
        return [TestBuildSanity()]

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Push tags."""
        version = get_project_version(project_root=docker_project_root)
        if (BRANCH == "main") ^ ("dev" in version):
            run_process(args=concatenate_args(args=["git", "tag", version]))
            run_process(args=concatenate_args(args=["git", "push", "--tags"]))
        else:
            raise Exception(f"Tag {version} is incompatible with branch {BRANCH}.")


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

    def run(self, non_docker_project_root: Path, docker_project_root: Path) -> None:
        """Modifies the appropriate files to start a new project."""
        master_project_settings = ProjectSettings.from_json(
            get_project_settings_json(project_root=docker_project_root).read_text()
        )
        pyproject_toml = get_pyproject_toml(project_root=docker_project_root)
        new_text = ""
        for line in pyproject_toml.open():
            if line == 'name = "template_python_project"\n':
                new_text += f'name = "{master_project_settings.name}"\n'
            elif line.startswith("version = "):
                new_text += 'version = "0.0.0"\n'
            else:
                new_text += line
        pyproject_toml.write_text(new_text)
