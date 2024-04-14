"""Abstract class for tasks that will be elements of the DAG."""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field, field_serializer, model_validator
from yaml import safe_dump, safe_load

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)


class BasicTaskInfo(BaseModel):
    """Dataclass for the info required to run any task."""

    non_docker_project_root: Path
    docker_project_root: Path
    local_uid: int = Field(gt=-1)
    local_gid: int = Field(gt=-1)
    local_user_env: dict[str, str] | None = None
    ci_cd_integration_test_mode: bool = False

    @model_validator(mode="after")
    def check_valid_local_user_env(self) -> "BasicTaskInfo":
        """Checks that local_user_env is only None when local_uid and local_gid are 0.

        Returns:
            BasicTaskInfo: Returns itself.
        """
        if self.local_user_env is None and not (
            self.local_uid == 0 and self.local_gid == 0
        ):
            msg = (
                "local_user_env can only be None when local_uid and local_gid are 0."
                " (root user)"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_valid_uid_gid_pair(self) -> "BasicTaskInfo":
        """Checks that if either uid or gid are 0 (root) the other one is too.

        Returns:
            BasicTaskInfo: Returns itself.
        """
        if (self.local_uid == 0) != (self.local_gid == 0):
            msg = (
                "When local_uid or local_gid are 0 (root user) the other must be too.\n"
                f"local_uid={self.local_uid}, local_gid={self.local_gid}"
            )
            raise ValueError(msg)
        return self

    @field_serializer("non_docker_project_root", "docker_project_root")
    def serialize_path_as_str(self, path: Path) -> str:
        """Serializes the path fields as strings.

        Args:
            path (Path): A path.

        Returns:
            str: A string representation of the path obj.
        """
        return str(path)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "BasicTaskInfo":
        """Builds an object from a YAML str.

        Args:
            yaml_str (str): String of the YAML representation of a BasicTaskInfo
                instance.

        Returns:
            BasicTaskInfo: A BasicTaskInfo object parsed from the YAML.
        """
        return BasicTaskInfo.model_validate(safe_load(yaml_str))

    def to_yaml(self) -> str:
        """Dumps object as a yaml str.

        Returns:
            str: A YAML representation of this ProjectSettings instance.
        """
        return safe_dump(self.model_dump())


class TaskNode(ABC):
    """An abstract representation of a task that can be run in a DAG."""

    non_docker_project_root: Path
    docker_project_root: Path
    local_uid: int
    local_gid: int
    local_user_env: dict[str, str] | None
    ci_cd_integration_test_mode: bool

    def __init__(self, basic_task_info: BasicTaskInfo) -> None:
        """Init method for TaskNode.

        Args:
            basic_task_info (BasicTaskInfo): The information needed to set up a task.

        Returns:
            None
        """
        self.non_docker_project_root = basic_task_info.non_docker_project_root
        self.docker_project_root = basic_task_info.docker_project_root
        self.local_uid = basic_task_info.local_uid
        self.local_gid = basic_task_info.local_gid
        self.local_user_env = basic_task_info.local_user_env
        self.ci_cd_integration_test_mode = basic_task_info.ci_cd_integration_test_mode

    def get_basic_task_info(self) -> BasicTaskInfo:
        """Get the basic info used to run this task.

        Returns:
            BasicTaskInfo: The basic info used to run this task.
        """
        return BasicTaskInfo(
            non_docker_project_root=self.non_docker_project_root,
            docker_project_root=self.docker_project_root,
            local_uid=self.local_uid,
            local_gid=self.local_gid,
            local_user_env=self.local_user_env,
            ci_cd_integration_test_mode=self.ci_cd_integration_test_mode,
        )

    def task_label(self) -> str:
        """A unique label for each task, used when building the DAG.

        Returns:
            str: The class name of the task.
        """
        return self.__class__.__name__

    def __eq__(self, other: object) -> bool:
        """Checks if this is equal to the other item.

        Args:
            other (object): The other object to compare equality with.

        Returns:
            bool: True if equal, otherwise false.
        """
        return isinstance(other, TaskNode) and self.task_label() == other.task_label()

    def __hash__(self) -> int:
        """Calculates a hash value for use in dictionaries.

        Returns:
            int: The hash value of this task.
        """
        return hash(self.task_label())

    @abstractmethod
    def required_tasks(self) -> list["TaskNode"]:
        """Will return the tasks required to start the current task.

        Returns:
            list[TaskNode]: A list of the tasks that must be completed
                before this one can be run.
        """

    @abstractmethod
    def run(self) -> None:
        """Will contain the logic of each task.

        Returns:
            None
        """


class PerSubprojectTask(TaskNode, ABC):
    """This abstract class is intended for tasks are repeated across subprojects."""

    subproject_context: SubprojectContext
    subproject: PythonSubproject

    def __init__(
        self,
        basic_task_info: BasicTaskInfo,
        subproject_context: SubprojectContext,
    ) -> None:
        """Init method for TaskNode.

        Args:
            basic_task_info (BasicTaskInfo): The information needed to set up a task.
            subproject_context (SubprojectContext): The subproject this task will
                execute logic for.

        Returns:
            None
        """
        super().__init__(basic_task_info=basic_task_info)
        self.subproject_context = subproject_context
        self.subproject = get_python_subproject(
            subproject_context=self.subproject_context,
            project_root=self.docker_project_root,
        )

    def task_label(self) -> str:
        """A unique label for each task, used when building the DAG.

        Returns:
            str: The class name of the task.
        """
        return f"{self.__class__.__name__}-{self.subproject_context.name}"
