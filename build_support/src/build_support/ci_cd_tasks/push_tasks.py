"""Should hold all tasks that push artifacts after testing."""

from pathlib import Path

from build_support.ci_cd_tasks.build_tasks import BuildPypi
from build_support.ci_cd_tasks.test_tasks import TestAll
from build_support.ci_cd_vars.git_status_vars import (
    current_branch_is_main,
    get_current_branch,
    get_git_diff,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_version,
    is_dev_project_version,
)
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class PushAll(TaskNode):
    """A collective push task used to push all elements of the project at once."""

    def required_tasks(self) -> list[TaskNode]:
        """Adds all required "sub-pushes" to the DAG."""
        return [PushTags(), PushPypi()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Does nothing."""


class PushTags(TaskNode):
    """Pushes tags to git, reserving the commit for a specific artifact push."""

    def required_tasks(self) -> list[TaskNode]:
        """Checks to see if the version is appropriate for the branch we are on."""
        return [TestAll()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Push tags."""
        current_branch = get_current_branch()
        current_version = get_project_version(project_root=docker_project_root)
        currently_on_main = current_branch_is_main(current_branch=current_branch)
        is_dev_version = is_dev_project_version(project_version=current_version)
        if currently_on_main ^ is_dev_version:
            local_user = f"{local_user_uid}:{local_user_gid}"
            run_process(
                args=concatenate_args(
                    args=[
                        "chown",
                        "-R",
                        local_user,
                        "/root/.gitconfig",
                    ]
                ),
                silent=True,
            )
            current_diff = get_git_diff()
            if current_diff:
                run_process(
                    args=concatenate_args(args=["git", "add", "-u"]),
                    local_user_uid=local_user_uid,
                    local_user_gid=local_user_gid,
                )
                run_process(
                    args=concatenate_args(
                        args=[
                            "git",
                            "commit",
                            "-m",
                            f"'Committing staged changes for {current_version}'",
                        ]
                    ),
                    local_user_uid=local_user_uid,
                    local_user_gid=local_user_gid,
                )
                run_process(
                    args=concatenate_args(args=["git", "push"]),
                    local_user_uid=local_user_uid,
                    local_user_gid=local_user_gid,
                )
            run_process(
                args=concatenate_args(args=["git", "tag", current_version]),
                local_user_uid=local_user_uid,
                local_user_gid=local_user_gid,
            )
            run_process(
                args=concatenate_args(args=["git", "push", "--tags"]),
                local_user_uid=local_user_uid,
                local_user_gid=local_user_gid,
            )
        else:
            raise ValueError(
                f"Tag {current_version} is incompatible with branch {current_branch}."
            )


class PushPypi(TaskNode):
    """Pushes the PyPi package.  Will move to combined once a repo is managed in Pulumi."""

    def required_tasks(self) -> list[TaskNode]:
        """Must build PyPi and push git tags before PyPi is pushed."""
        return [PushTags(), BuildPypi()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Push PyPi."""