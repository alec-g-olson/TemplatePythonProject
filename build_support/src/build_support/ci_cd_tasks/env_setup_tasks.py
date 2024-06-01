"""Holds all tasks that setup environments during the build process.

Attributes:
    | GIT_BRANCH_NAME_REGEX:  The regex we use to extract the ticket ID from branch
        names.
"""

import re
from typing import override

from pydantic import BaseModel, Field
from yaml import safe_dump, safe_load

from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_build_command
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_dir,
    get_git_info_yaml,
)
from build_support.ci_cd_vars.git_status_vars import (
    get_current_branch_name,
    get_local_tags,
    git_fetch,
)
from build_support.ci_cd_vars.project_setting_vars import get_pulumi_version
from build_support.ci_cd_vars.project_structure import (
    get_integration_test_scratch_folder,
)
from build_support.process_runner import run_process


class SetupDevEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running dev commands."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build a dev environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a dev env. (Empty)
        """
        return []

    @override
    def run(self) -> None:
        """Builds a stable environment for running dev commands.

        Returns:
            None
        """
        if not self.ci_cd_integration_test_mode:
            run_process(
                args=get_docker_build_command(
                    docker_project_root=self.docker_project_root,
                    target_image=DockerTarget.DEV,
                    extra_args={
                        "--build-arg": [
                            "DOCKER_REMOTE_PROJECT_ROOT="
                            + str(self.docker_project_root.absolute()),
                        ],
                    },
                ),
            )


class SetupProdEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running prod commands."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build a prod environment.

        Returns:
            list[TaskNode]: A list of tasks required to build a prod env. (Empty)
        """
        return []

    @override
    def run(self) -> None:
        """Builds a stable environment for running prod commands.

        Returns:
            None
        """
        if not self.ci_cd_integration_test_mode:
            run_process(
                args=get_docker_build_command(
                    docker_project_root=self.docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
            )


class SetupInfraEnvironment(TaskNode):
    """Builds a docker image with a stable environment for running infra commands."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of tasks to run before we can build an infra environment.

        Returns:
            list[TaskNode]: A list of tasks required to build an infra env. (Empty)
        """
        return []

    @override
    def run(self) -> None:
        """Builds a stable environment for running infra commands.

        Returns:
            None
        """
        if not self.ci_cd_integration_test_mode:
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

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the list of tasks to run before cleaning.

        Returns:
            list[TaskNode]: A list of tasks required to clean project. (Empty)
        """
        return []

    @override
    def run(self) -> None:
        """Deletes all the temporary build files.

        Returns:
            None
        """
        run_process(
            args=["rm", "-rf", get_build_dir(project_root=self.docker_project_root)],
        )
        run_process(
            args=[
                "rm",
                "-rf",
                get_integration_test_scratch_folder(
                    project_root=self.docker_project_root
                ),
            ],
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


GIT_BRANCH_NAME_REGEX = r"^([^-]+)-?.*$"


class GitInfo(BaseModel):
    """An object containing the current git information."""

    branch: str = Field(pattern=GIT_BRANCH_NAME_REGEX)
    tags: list[str]

    @staticmethod
    def get_primary_branch_name() -> str:
        """Gets the primary branch name for the repo.

        Returns:
            str: The primary branch name for this repo.
        """
        return "main"

    def get_ticket_id(self) -> str | None:
        """Extracts the ticket id from the branch name.

        Returns:
            str: The id of the ticket associated with the branch.
        """
        match = re.search(pattern=GIT_BRANCH_NAME_REGEX, string=self.branch)
        ticket_id = match.group(1) if match is not None else None
        return (
            ticket_id
            if ticket_id is not None and ticket_id != self.get_primary_branch_name()
            else None
        )

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

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Gets the list of tasks to run before getting git info.

        Returns:
            list[TaskNode]: A list of tasks required to get git info. (Empty)
        """
        return []

    @override
    def run(self) -> None:
        """Builds a yaml with required git info.

        Returns:
            None
        """
        git_fetch(
            project_root=self.docker_project_root,
            local_uid=self.local_uid,
            local_gid=self.local_gid,
            local_user_env=self.local_user_env,
        )
        get_git_info_yaml(project_root=self.docker_project_root).write_text(
            GitInfo(
                branch=get_current_branch_name(project_root=self.docker_project_root),
                tags=get_local_tags(project_root=self.docker_project_root),
            ).to_yaml(),
        )
