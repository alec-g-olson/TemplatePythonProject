"""A module for running tasks that are not domain specific."""

import json
from dataclasses import dataclass
from pathlib import Path

from common_vars import (
    THREADS_AVAILABLE,
    DockerTarget,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
    get_base_docker_command_for_image,
    get_build_dir,
    get_build_src_dir,
    get_build_test_dir,
    get_current_branch,
    get_docker_build_command,
    get_docker_command_for_image,
    get_docker_image,
    get_git_info_json,
    get_mypy_path_env,
    get_project_name,
    get_project_version,
    get_pulumi_dir,
    get_pulumi_version,
    get_pypi_src_and_test,
    get_pypi_src_dir,
)
from dag_engine import (
    TaskNode,
    concatenate_args,
    get_output_of_process,
    run_process,
    run_process_as_local_user,
)


class BuildDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Builds a stable environment for running dev commands."""
        run_process(
            args=get_docker_build_command(
                project_root=docker_project_root, target_image=DockerTarget.DEV
            )
        )


class BuildProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Builds a stable environment for running prod commands."""
        run_process(
            args=get_docker_build_command(
                project_root=docker_project_root, target_image=DockerTarget.PROD
            )
        )


class BuildPulumiEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running pulumi commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Check to make sure we are logged into docker."""
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Builds a stable environment for running pulumi commands."""
        run_process(
            args=get_docker_build_command(
                project_root=docker_project_root,
                target_image=DockerTarget.PULUMI,
                extra_args={
                    "--build-arg": "PULUMI_VERSION="
                    + get_pulumi_version(project_root=docker_project_root)
                },
            )
        )


class Clean(TaskNode):
    """Removes all temporary files for a clean build environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
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

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Builds a json with required git info."""
        run_process_as_local_user(
            args=concatenate_args(args=["git", "fetch"]),
            local_username=local_username,
        )
        get_git_info_json(project_root=docker_project_root).parent.mkdir(
            parents=True, exist_ok=True
        )
        get_git_info_json(project_root=docker_project_root).write_text(
            GitInfo(
                branch=get_current_branch(),
                tags=get_output_of_process(["git", "tag"], silent=True).split("\n"),
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

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Runs tests in the build_test folder."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    get_build_test_dir(project_root=docker_project_root),
                ]
            )
        )


def get_bandit_pypi_report_name(project_root: Path) -> str:
    """Get the name of the pypi bandit security report."""
    return (
        get_project_name(project_root=project_root)
        + "_pypi_bandit_report_"
        + get_project_version(project_root=project_root)
        + ".txt"
    )


def get_bandit_pypi_report_path(project_root: Path) -> Path:
    """Get the path of the pulumi bandit security report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_bandit_pypi_report_name(project_root=project_root)
    )


def get_bandit_pulumi_report_name(project_root: Path) -> str:
    """Get the name of the pypi bandit security report."""
    return (
        get_project_name(project_root=project_root)
        + "_pulumi_bandit_report_"
        + get_project_version(project_root=project_root)
        + ".txt"
    )


def get_bandit_pulumi_report_path(project_root: Path) -> Path:
    """Get the path of the pulumi bandit security report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_bandit_pulumi_report_name(project_root=project_root)
    )


def get_bandit_build_support_report_name(project_root: Path) -> str:
    """Get the name of the pypi bandit security report."""
    return (
        get_project_name(project_root=project_root)
        + "_build_support_bandit_report_"
        + get_project_version(project_root=project_root)
        + ".txt"
    )


def get_bandit_build_support_report_path(project_root: Path) -> Path:
    """Get the path of the pulumi bandit security report."""
    return get_build_dir(project_root=project_root).joinpath(
        get_bandit_build_support_report_name(project_root=project_root)
    )


class TestPythonStyle(TaskNode):
    """Task enforcing stylistic checks of python code."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures the dev environment is present before running style checks."""
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Runs all stylistic checks on code."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
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
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
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
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "pydocstyle",
                    get_all_src_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
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
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "flake8",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=non_docker_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image(
                    project_root=docker_project_root, target_image=DockerTarget.DEV
                ),
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
        run_process(
            args=concatenate_args(
                args=[
                    mypy_command,
                    get_pulumi_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "bandit",
                    "-o",
                    get_bandit_pypi_report_path(project_root=docker_project_root),
                    "-r",
                    get_pypi_src_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "bandit",
                    "-o",
                    get_bandit_pulumi_report_path(project_root=docker_project_root),
                    "-r",
                    get_pulumi_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "bandit",
                    "-o",
                    get_bandit_build_support_report_path(
                        project_root=docker_project_root
                    ),
                    "-r",
                    get_build_src_dir(project_root=docker_project_root),
                ]
            )
        )


class Lint(TaskNode):
    """Linting task."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure dev environment has been built before linting."""
        return [BuildDevEnvironment()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Lints all python files in project."""
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "isort",
                    get_all_python_folders(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.DEV,
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

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_username: str,
    ) -> None:
        """Push tags."""
        branch = get_current_branch()
        version = get_project_version(project_root=docker_project_root)
        if (branch == "main") ^ ("dev" in version):
            current_diff = get_output_of_process(
                args=concatenate_args(args=["git", "diff"])
            )
            if current_diff:
                run_process_as_local_user(
                    args=concatenate_args(args=["git", "add", "-u"]),
                    local_username=local_username,
                )
                run_process_as_local_user(
                    args=concatenate_args(
                        args=[
                            "git",
                            "commit",
                            "-m",
                            f"'Committing staged changes for {version}'",
                        ]
                    ),
                    local_username=local_username,
                )
                run_process_as_local_user(
                    args=concatenate_args(args=["git", "push"]),
                    local_username=local_username,
                )
            run_process(args=concatenate_args(args=["git", "tag", version]))
            run_process_as_local_user(
                args=concatenate_args(args=["git", "push", "--tags"]),
                local_username=local_username,
            )
        else:
            raise Exception(f"Tag {version} is incompatible with branch {branch}.")
