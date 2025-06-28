"""Should hold all tasks that push artifacts after testing."""

from typing import override

from build_support.ci_cd_tasks.build_tasks import BuildPypi
from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_tasks.validation_tasks import ValidateAll
from build_support.ci_cd_vars.git_status_vars import (
    commit_changes_if_diff,
    current_branch_is_main,
    get_current_branch_name,
    tag_current_commit_and_push,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_version,
    is_dev_project_version,
)


class PushAll(TaskNode):
    """A collective push task used to push all elements of the project at once."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Lists all "sub-pushes" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [
            PushTags(basic_task_info=self.get_basic_task_info()),
            PushPypi(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Arguments are inherited from subclass.

        Returns:
            None
        """


class PushTags(TaskNode):
    """Pushes tags to git, reserving the commit for a specific artifact push."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can push version tags.

        Returns:
            list[TaskNode]: A list of tasks required to push version tags.
        """
        return [ValidateAll(basic_task_info=self.get_basic_task_info())]

    @override
    def run(self) -> None:
        """Tags commit with version and pushes tag to origin.

        This task must be run before any other artifacts are pushed.  This is so
        if any artifacts are pushed anyone can easily find the commit they were
        built from.  If tags are pushed after some artifacts are built it would
        be possible for a build error to cause the tag to not be pushed. If that
        happened then the version check we do during testing would be invalid
        because there could have previously been artifacts pushed for a version that
        passes that test.

        Returns:
            None
        """
        current_version = get_project_version(project_root=self.docker_project_root)
        currently_on_main = current_branch_is_main(
            project_root=self.docker_project_root
        )
        is_dev_version = is_dev_project_version(project_version=current_version)
        if currently_on_main ^ is_dev_version:
            commit_changes_if_diff(
                commit_message=f"Committing staged changes for {current_version}",
                project_root=self.docker_project_root,
                local_uid=self.local_uid,
                local_gid=self.local_gid,
                local_user_env=self.local_user_env,
            )
            tag_current_commit_and_push(
                tag=current_version,
                project_root=self.docker_project_root,
                local_uid=self.local_uid,
                local_gid=self.local_gid,
                local_user_env=self.local_user_env,
            )
        else:
            current_branch = get_current_branch_name(
                project_root=self.docker_project_root
            )
            msg = f"Tag {current_version} is incompatible with branch {current_branch}."
            raise ValueError(msg)


class PushPypi(TaskNode):
    """Pushes the PyPi package."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can push a pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to push the Pypi package.
        """
        return [
            PushTags(basic_task_info=self.get_basic_task_info()),
            BuildPypi(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Push PyPi.

        Returns:
            None
        """
