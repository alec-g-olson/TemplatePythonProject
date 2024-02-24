"""env_setup_tasks should hold all tasks that setup environments during the build process."""

from pathlib import Path

from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_build_command
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_dir,
    get_build_support_docs_build_dir,
    get_build_support_docs_src_dir,
    get_git_info_yaml,
    get_pypi_docs_build_dir,
    get_pypi_docs_src_dir,
)
from build_support.ci_cd_vars.git_status_vars import get_current_branch, get_local_tags
from build_support.ci_cd_vars.project_setting_vars import get_pulumi_version
from build_support.dag_engine import TaskNode, concatenate_args, run_process
from pydantic import BaseModel
from yaml import safe_dump, safe_load


class BuildDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build a dev environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a dev env. (Empty)
        """
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds a stable environment for running dev commands.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
        run_process(
            args=get_docker_build_command(
                project_root=docker_project_root, target_image=DockerTarget.DEV
            )
        )


class BuildProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build a prod environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a prod env. (Empty)
        """
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds a stable environment for running prod commands.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
        run_process(
            args=get_docker_build_command(
                project_root=docker_project_root, target_image=DockerTarget.PROD
            )
        )


class BuildPulumiEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running pulumi commands."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build a pulumi environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a pulumi env. (Empty)
        """
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds a stable environment for running pulumi commands.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
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
        """Gets the list of tasks to run before cleaning.

        Returns:
            list[TaskNode]: A list of tasks required to clean project. (Empty)
        """
        return []

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Deletes all the temporary build files.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
        run_process(args=["rm", "-rf", get_build_dir(project_root=docker_project_root)])
        for docs_build_dir in [
            get_build_support_docs_build_dir(project_root=docker_project_root),
            get_pypi_docs_build_dir(project_root=docker_project_root),
        ]:
            run_process(args=["rm", "-rf", docs_build_dir])
        for docs_source_dir in [
            get_build_support_docs_src_dir(project_root=docker_project_root),
            get_pypi_docs_src_dir(project_root=docker_project_root),
        ]:
            files_and_folders_to_remove = [
                file_or_folder_path
                for file_or_folder_path in docs_source_dir.glob("*")
                if file_or_folder_path.name != "index.rst"
            ]
            run_process(
                args=concatenate_args(args=["rm", "-rf", files_and_folders_to_remove])
            )


class GitInfo(BaseModel):
    """An object containing the current git information."""

    branch: str
    tags: list[str]

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "GitInfo":
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

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds a yaml with required git info.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
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
