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
        """Lists all "sub-pushes" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [PushTags(), PushPypi()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Does nothing.

        Arguments are inherited from sub-class.

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """


class PushTags(TaskNode):
    """Pushes tags to git, reserving the commit for a specific artifact push."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can push version tags.

        Returns:
            list[TaskNode]: A list of tasks required to push version tags.
        """
        return [TestAll()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Tags commit with versio and pushes tag to origin.

        This task must be run before any other artifacts are pushed.  This is so
        if any artifacts are pushed anyone can easily find the commit they were
        built from.  If tags are pushed after some artifacts are built it would
        be possible for a build error to cause the tag to not be pushed. If that
        happened then the version check we do during testing would be invalid
        because there could previously pushed artifacts for a version that passes
        that test.

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
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
        """Get the list of task that need to be run before we can push a pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to push the Pypi package.
        """
        return [PushTags(), BuildPypi()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Push PyPi.

        Arguments:
            non_docker_project_root (Path): Path to this project's root when running
                in docker containers.
            docker_project_root (Path): Path to this project's root on the local
                machine.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
