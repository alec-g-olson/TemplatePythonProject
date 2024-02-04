"""env_setup_tasks should hold all tasks that setup environments during the build process."""

from dataclasses import dataclass
from pathlib import Path

from build_vars.docker_vars import DockerTarget, get_docker_build_command
from build_vars.file_and_dir_path_vars import get_build_dir, get_git_info_yaml
from build_vars.git_status_vars import get_current_branch, get_local_tags
from build_vars.project_setting_vars import get_pulumi_version
from dag_engine import (
    TaskNode,
    concatenate_args,
    run_process,
    run_process_as_local_user,
)
from yaml import safe_dump, safe_load


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
    def from_yaml(cls, yaml_str: str) -> "GitInfo":
        """Builds an object from a json str."""
        yaml_vals = safe_load(yaml_str)
        git_info = GitInfo(**yaml_vals)
        git_info._validate_settings()
        return git_info

    def to_yaml(self) -> str:
        """Dumps object as a yaml str."""
        return safe_dump(self.__dict__)

    def _validate_settings(self):
        """Validates the values in this instance of GitInfo."""
        if not isinstance(self.branch, str):
            raise ValueError(
                '"branch" in git info must have a string value, '
                f"found type {self.branch.__class__.__name__}."
            )
        if not isinstance(self.tags, list):
            raise ValueError(
                '"tags" in git info must be a list, '
                f"found type {self.tags.__class__.__name__}."
            )
        if not all(isinstance(tag, str) for tag in self.tags):
            types = {tag.__class__.__name__ for tag in self.tags}
            raise ValueError(
                'All elements of "tags" in git info must be a string, '
                f"found types {','.join(sorted(list(types)))}."
            )


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
        get_git_info_yaml(project_root=docker_project_root).write_text(
            GitInfo(
                branch=get_current_branch(),
                tags=get_local_tags(),
            ).to_yaml()
        )