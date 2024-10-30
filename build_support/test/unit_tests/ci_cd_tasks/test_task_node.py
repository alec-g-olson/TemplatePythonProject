from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import pytest
import yaml
from _pytest.fixtures import SubRequest
from pydantic import ValidationError

from build_support.ci_cd_tasks.task_node import (
    BasicTaskInfo,
    PerSubprojectTask,
    TaskNode,
)
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)


@pytest.fixture(
    params=[
        {
            "ci_cd_feature_test_mode": False,
            "docker_project_root": "/usr/dev",
            "local_gid": 2,
            "local_uid": 1,
            "local_user_env": {"ENV1": "VAL1", "ENV2": "VAL2"},
            "non_docker_project_root": "/some/local/user/path/to/project",
        },
        {
            "ci_cd_feature_test_mode": False,
            "docker_project_root": "/usr/dev",
            "local_gid": 0,
            "local_uid": 0,
            "local_user_env": None,
            "non_docker_project_root": "/some/local/user/path/to/project",
        },
        {
            "docker_project_root": "/usr/dev",
            "local_gid": 1,
            "local_uid": 2,
            "local_user_env": {"ENV1": "VAL1", "ENV2": "VAL2"},
            "non_docker_project_root": "/some/local/user/path/to/project",
        },
        {
            "ci_cd_feature_test_mode": False,
            "docker_project_root": "/usr/dev",
            "local_gid": 0,
            "local_uid": 0,
            "non_docker_project_root": "/some/local/user/path/to/project",
        },
    ]
)
def basic_task_info_data_dict(request: SubRequest) -> dict[str, Any]:
    return cast(dict[str, Any], request.param)


@pytest.fixture()
def basic_task_info_yaml_str(basic_task_info_data_dict: dict[str, Any]) -> str:
    data_copy = deepcopy(basic_task_info_data_dict)
    if "ci_cd_feature_test_mode" not in data_copy:
        data_copy["ci_cd_feature_test_mode"] = False
    if "local_user_env" not in data_copy:
        data_copy["local_user_env"] = None
    return yaml.dump(data_copy)


def test_load(
    basic_task_info_yaml_str: str, basic_task_info_data_dict: dict[str, Any]
) -> None:
    basic_task_info = BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)
    assert basic_task_info == BasicTaskInfo.model_validate(basic_task_info_data_dict)


def test_load_bad_non_docker_project_root(
    basic_task_info_data_dict: dict[str, Any],
) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["non_docker_project_root"] = 4
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_docker_project_root(
    basic_task_info_data_dict: dict[str, Any],
) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["docker_project_root"] = 4
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_uid_str(basic_task_info_data_dict: dict[str, Any]) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["local_uid"] = "twenty"
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_uid_bad_int(basic_task_info_data_dict: dict[str, Any]) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["local_uid"] = -5
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_gid_str(basic_task_info_data_dict: dict[str, Any]) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["local_gid"] = "twenty"
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_gid_bad_int(basic_task_info_data_dict: dict[str, Any]) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["local_gid"] = -5
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_user_env(basic_task_info_data_dict: dict[str, Any]) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["local_user_env"] = 8
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_ci_cd_feature_test_mode(
    basic_task_info_data_dict: dict[str, Any],
) -> None:
    data_copy = deepcopy(basic_task_info_data_dict)
    data_copy["ci_cd_feature_test_mode"] = "Probably"
    basic_task_info_yaml_str = yaml.dump(data_copy)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_uid_gid_pair_uid_0() -> None:
    basic_task_info_data_dict = {
        "ci_cd_feature_test_mode": False,
        "docker_project_root": "/usr/dev",
        "local_gid": 2,
        "local_uid": 0,
        "local_user_env": {"ENV1": "VAL1", "ENV2": "VAL2"},
        "non_docker_project_root": "/some/local/user/path/to/project",
    }
    basic_task_info_yaml_str = yaml.dump(basic_task_info_data_dict)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_uid_gid_pair_gid_0() -> None:
    basic_task_info_data_dict = {
        "ci_cd_feature_test_mode": False,
        "docker_project_root": "/usr/dev",
        "local_gid": 0,
        "local_uid": 1,
        "local_user_env": {"ENV1": "VAL1", "ENV2": "VAL2"},
        "non_docker_project_root": "/some/local/user/path/to/project",
    }
    basic_task_info_yaml_str = yaml.dump(basic_task_info_data_dict)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_load_bad_local_user_env_for_non_root() -> None:
    basic_task_info_data_dict = {
        "ci_cd_feature_test_mode": False,
        "docker_project_root": "/usr/dev",
        "local_gid": 2,
        "local_uid": 1,
        "local_user_env": None,
        "non_docker_project_root": "/some/local/user/path/to/project",
    }
    basic_task_info_yaml_str = yaml.dump(basic_task_info_data_dict)
    with pytest.raises(ValidationError):
        BasicTaskInfo.from_yaml(yaml_str=basic_task_info_yaml_str)


def test_dump(
    basic_task_info_yaml_str: str, basic_task_info_data_dict: dict[str, Any]
) -> None:
    basic_task_info = BasicTaskInfo.model_validate(basic_task_info_data_dict)
    assert basic_task_info.to_yaml() == basic_task_info_yaml_str


expected_non_docker_project_root = Path("/non/docker/project/root")
expected_docker_project_root = Path("/docker/project/root")

expected_basic_task_info = BasicTaskInfo(
    non_docker_project_root=expected_non_docker_project_root,
    docker_project_root=expected_docker_project_root,
    local_uid=10,
    local_gid=2,
    local_user_env={"ENV1": "VAL1", "ENV2": "VAL2"},
)


def build_mock_basic_task(
    task_name: str, required_mock_tasks: list[TaskNode]
) -> TaskNode:
    """Builds a mock task for testing task interactions."""

    return type(  # type: ignore[no-any-return]
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

    return type(  # type: ignore[no-any-return]
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
