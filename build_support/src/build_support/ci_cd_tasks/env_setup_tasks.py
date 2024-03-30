"""Holds all tasks that setup environments during the build process."""

from grp import getgrgid
from pwd import getpwuid

from pydantic import BaseModel
from yaml import safe_dump, safe_load

from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_build_command
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_dir,
    get_git_info_yaml,
)
from build_support.ci_cd_vars.git_status_vars import get_current_branch, get_local_tags
from build_support.ci_cd_vars.project_setting_vars import get_pulumi_version
from build_support.process_runner import concatenate_args, run_process


class SetupDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build a dev environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a dev env. (Empty)
        """
        return []

    def run(self) -> None:
        """Builds a stable environment for running dev commands.

        Returns:
            None
        """
        run_process(
            args=get_docker_build_command(
                docker_project_root=self.docker_project_root,
                target_image=DockerTarget.DEV,
                extra_args={
                    "--build-arg": [
                        "DOCKER_REMOTE_PROJECT_ROOT="
                        + str(self.docker_project_root.absolute()),
                        f"CURRENT_USER={getpwuid(self.local_user_uid).pw_name}",
                        f"CURRENT_GROUP={getgrgid(self.local_user_gid).gr_name}",
                        f"CURRENT_USER_ID={self.local_user_uid}",
                        f"CURRENT_GROUP_ID={self.local_user_gid}",
                    ],
                },
            ),
        )


class SetupProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build a prod environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a prod env. (Empty)
        """
        return []

    def run(self) -> None:
        """Builds a stable environment for running prod commands.

        Returns:
            None
        """
        run_process(
            args=get_docker_build_command(
                docker_project_root=self.docker_project_root,
                target_image=DockerTarget.PROD,
            ),
        )


class SetupInfraEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running infra commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build a infra environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a infra env. (Empty)
        """
        return []

    def run(self) -> None:
        """Builds a stable environment for running infra commands.

        Returns:
            None
        """
        run_process(
            args=get_docker_build_command(
                docker_project_root=self.docker_project_root,
                target_image=DockerTarget.INFRA,
                extra_args={
                    "--build-arg": "PULUMI_VERSION="
                    + get_pulumi_version(project_root=self.docker_project_root),
                },
            ),
        )


class Clean(TaskNode):
    """Removes all temporary files for a clean build environment."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the list of tasks to run before cleaning.

        Returns:
            list[TaskNode]: A list of tasks required to clean project. (Empty)
        """
        return []

    def run(self) -> None:
        """Deletes all the temporary build files.

        Returns:
            None
        """
        run_process(
            args=["rm", "-rf", get_build_dir(project_root=self.docker_project_root)],
        )
        run_process(
            args=["rm", "-rf", self.docker_project_root.joinpath(".mypy_cache")],
        )
        run_process(
            args=["rm", "-rf", self.docker_project_root.joinpath(".pytest_cache")],
        )
        run_process(
            args=["rm", "-rf", self.docker_project_root.joinpath(".ruff_cache")],
        )


class GitInfo(BaseModel):
    """An object containing the current git information."""

    branch: str
    tags: list[str]

    @staticmethod
    def from_yaml(yaml_str: str) -> "GitInfo":
        """Builds an object from a json str.

        Args:
            yaml_str (str): String of the YAML representation of a GitInfo instance.

        Returns:
            GitInfo: A GitInfo object parsed from the YAML.
        """
        return GitInfo.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str.

        Returns:
            str: A YAML representation of this GitInfo instance.
        """
        return safe_dump(self.model_dump())


class GetGitInfo(TaskNode):
    """Gets all git info we could need for checks during building."""

    def required_tasks(self) -> list[TaskNode]:
        """Gets the list of tasks to run before getting git info.

        Returns:
            list[TaskNode]: A list of tasks required to get git info. (Empty)
        """
        return []

    def run(self) -> None:
        """Builds a yaml with required git info.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(args=["git", "fetch"]),
            user_uid=self.local_user_uid,
            user_gid=self.local_user_gid,
        )
        get_git_info_yaml(project_root=self.docker_project_root).write_text(
            GitInfo(
                branch=get_current_branch(
                    local_user_uid=self.local_user_uid,
                    local_user_gid=self.local_user_gid,
                ),
                tags=get_local_tags(
                    local_user_uid=self.local_user_uid,
                    local_user_gid=self.local_user_gid,
                ),
            ).to_yaml(),
        )
