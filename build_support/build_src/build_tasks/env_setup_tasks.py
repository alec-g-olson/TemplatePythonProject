"""env_setup_tasks should hold all tasks that setup environments during the build process."""

from pathlib import Path

from build_vars.docker_vars import DockerTarget, get_docker_build_command
from build_vars.file_and_dir_path_vars import get_build_dir, get_git_info_yaml
from build_vars.git_status_vars import get_current_branch, get_local_tags
from build_vars.project_setting_vars import get_pulumi_version
from dag_engine import TaskNode, concatenate_args, run_process
from pydantic import BaseModel
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
        local_user_uid: int,
        local_user_gid: int,
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
        local_user_uid: int,
        local_user_gid: int,
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
        local_user_uid: int,
        local_user_gid: int,
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
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Deletes all the temporary build files."""
        run_process(args=["rm", "-rf", get_build_dir(project_root=docker_project_root)])


class GitInfo(BaseModel):
    """An object containing the current git information."""

    branch: str
    tags: list[str]

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "GitInfo":
        """Builds an object from a json str."""
        return GitInfo.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str."""
        return safe_dump(self.model_dump())


class GetGitInfo(TaskNode):
    """Gets all git info we could need for checks during building."""

    def required_tasks(self) -> list[TaskNode]:
        """Nothing required."""
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds a json with required git info."""
        run_process(
            args=concatenate_args(args=["git", "fetch"]),
            local_user_uid=local_user_uid,
            local_user_gid=local_user_gid,
        )
        get_git_info_yaml(project_root=docker_project_root).write_text(
            GitInfo(
                branch=get_current_branch(),
                tags=get_local_tags(),
            ).to_yaml()
        )
