from pathlib import Path
from unittest.mock import Mock

from build_support.ci_cd_tasks.task_node import (
    BasicTaskInfo,
    PerSubprojectTask,
    TaskNode,
)
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)

expected_non_docker_project_root = Path("/non/docker/project/root")
expected_docker_project_root = Path("/docker/project/root")
expected_local_user_uid = 42
expected_local_user_gid = 10

expected_basic_task_info = BasicTaskInfo(
    non_docker_project_root=expected_non_docker_project_root,
    docker_project_root=expected_docker_project_root,
    local_user_uid=expected_local_user_uid,
    local_user_gid=expected_local_user_gid,
)


def build_mock_basic_task(
    task_name: str, required_mock_tasks: list[TaskNode]
) -> TaskNode:
    """Builds a mock task for testing task interactions."""

    return type(
        task_name,
        (TaskNode,),
        {
            "required_tasks": Mock(return_value=required_mock_tasks),
            "run": Mock(),
        },
    )(basic_task_info=expected_basic_task_info)


def build_mock_per_subproject_task(
    task_name: str,
    required_mock_tasks: list[TaskNode],
    subproject_context: SubprojectContext,
) -> PerSubprojectTask:
    """Builds a mock task for testing task interactions."""

    return type(
        task_name,
        (PerSubprojectTask,),
        {
            "required_tasks": Mock(return_value=required_mock_tasks),
            "run": Mock(),
        },
    )(
        basic_task_info=expected_basic_task_info,
        subproject_context=subproject_context,
    )


def test_task_init() -> None:
    task_name = "test_task_init"
    mock_task = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task.non_docker_project_root == expected_non_docker_project_root
    assert mock_task.docker_project_root == expected_docker_project_root
    assert mock_task.local_user_uid == expected_local_user_uid
    assert mock_task.local_user_gid == expected_local_user_gid


def test_task_required_tasks() -> None:
    no_requirement_name = "test_task_no_requirements"
    no_requirement_task = build_mock_basic_task(
        task_name=no_requirement_name, required_mock_tasks=[]
    )
    assert no_requirement_task.required_tasks() == []
    one_requirement_name = "test_task_no_requirements"
    one_requirement_task = build_mock_basic_task(
        task_name=one_requirement_name, required_mock_tasks=[no_requirement_task]
    )
    assert one_requirement_task.required_tasks() == [no_requirement_task]
    assert no_requirement_task.required_tasks() == []


def test_task_run_callable() -> None:
    task_name = "test_task_run"
    mock_task = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    mock_task.run()
    assert True


def test_task_hash() -> None:
    task_name = "test_task_hash"
    mock_task = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task.__hash__() == hash(mock_task.task_label())


def test_task_eq() -> None:
    task_name = "test_task_eq"
    mock_task_1 = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    mock_task_2 = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task_1 == mock_task_2


def test_task_ne() -> None:
    mock_task_1 = build_mock_basic_task(task_name="task_1", required_mock_tasks=[])
    mock_task_2 = build_mock_basic_task(task_name="task_2", required_mock_tasks=[])
    assert mock_task_1 != mock_task_2


def test_get_basic_task_info() -> None:
    task_name = "test_task_get_basic_info"
    mock_task = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task.get_basic_task_info() == expected_basic_task_info


def test_task_label() -> None:
    task_name = "test_task_label"
    mock_task = build_mock_basic_task(task_name=task_name, required_mock_tasks=[])
    assert mock_task.task_label() == task_name


def test_subproject_task_required_tasks(subproject_context: SubprojectContext) -> None:
    no_requirement_name = "test_task_no_requirements"
    no_requirement_task = build_mock_basic_task(
        task_name=no_requirement_name, required_mock_tasks=[]
    )
    assert no_requirement_task.required_tasks() == []
    one_requirement_name = "test_task_no_requirements"
    one_requirement_task = build_mock_per_subproject_task(
        task_name=one_requirement_name,
        required_mock_tasks=[no_requirement_task],
        subproject_context=subproject_context,
    )
    assert one_requirement_task.required_tasks() == [no_requirement_task]
    assert no_requirement_task.required_tasks() == []


def test_subproject_task_run_callable(subproject_context: SubprojectContext) -> None:
    task_name = "test_task_run"
    mock_task = build_mock_per_subproject_task(
        task_name=task_name,
        required_mock_tasks=[],
        subproject_context=subproject_context,
    )
    mock_task.run()
    assert True


def test_subproject_task_init(subproject_context: SubprojectContext) -> None:
    task_name = "test_subproject_task_init"
    mock_task = build_mock_per_subproject_task(
        task_name=task_name,
        required_mock_tasks=[],
        subproject_context=subproject_context,
    )
    assert mock_task.non_docker_project_root == expected_non_docker_project_root
    assert mock_task.docker_project_root == expected_docker_project_root
    assert mock_task.local_user_uid == expected_local_user_uid
    assert mock_task.local_user_gid == expected_local_user_gid
    assert mock_task.subproject_context == subproject_context
    assert mock_task.subproject == get_python_subproject(
        subproject_context=subproject_context,
        project_root=expected_docker_project_root,
    )


def test_subproject_task_label(subproject_context: SubprojectContext) -> None:
    task_name = "test_subproject_task_label"
    mock_task = build_mock_per_subproject_task(
        task_name=task_name,
        required_mock_tasks=[],
        subproject_context=subproject_context,
    )
    assert mock_task.task_label() == f"{task_name}-{subproject_context.name}"
