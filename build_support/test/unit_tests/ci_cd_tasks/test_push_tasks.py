from unittest.mock import patch

import pytest
from test_utils.empty_function_check import (  # type: ignore[import-untyped]
    is_an_empty_function,
)

from build_support.ci_cd_tasks.build_tasks import BuildPypi
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi, PushTags
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import ValidateAll
from build_support.ci_cd_vars.git_status_vars import MAIN_BRANCH_NAME


def test_push_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushAll(basic_task_info=basic_task_info).required_tasks() == [
        PushTags(basic_task_info=basic_task_info),
        PushPypi(basic_task_info=basic_task_info),
    ]


def test_run_push_all(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(func=PushAll(basic_task_info=basic_task_info).run)


def test_push_tags_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushTags(basic_task_info=basic_task_info).required_tasks() == [
        ValidateAll(basic_task_info=basic_task_info)
    ]


@pytest.mark.parametrize(
    ("branch_name", "current_version"),
    [(MAIN_BRANCH_NAME, "0.0.1-dev.1"), ("not_" + MAIN_BRANCH_NAME, "0.0.1")],
)
def test_run_push_tags_not_allowed(
    basic_task_info: BasicTaskInfo, branch_name: str, current_version: str
) -> None:
    with (
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_current_branch_name"
        ) as get_branch_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.current_branch_is_main"
        ) as is_on_main_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_project_version"
        ) as get_version_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.commit_changes_if_diff"
        ) as commit_changes_mock,
    ):
        is_on_main_mock.return_value = branch_name == MAIN_BRANCH_NAME
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        expected_message = (
            f"Tag {current_version} is incompatible with branch {branch_name}."
        )
        with pytest.raises(ValueError, match=expected_message):
            PushTags(basic_task_info=basic_task_info).run()
        commit_changes_mock.assert_not_called()


@pytest.mark.parametrize(
    ("branch_name", "current_version"),
    [(MAIN_BRANCH_NAME, "0.0.1"), ("not_" + MAIN_BRANCH_NAME, "0.0.1-dev.1")],
)
def test_run_push_tags_allowed(
    basic_task_info: BasicTaskInfo, branch_name: str, current_version: str
) -> None:
    with (
        patch(
            "build_support.ci_cd_tasks.push_tasks.tag_current_commit_and_push"
        ) as tag_and_push_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.commit_changes_if_diff"
        ) as commit_changes_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.current_branch_is_main"
        ) as is_on_main_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_project_version"
        ) as get_version_mock,
    ):
        is_on_main_mock.return_value = branch_name == MAIN_BRANCH_NAME
        get_version_mock.return_value = current_version
        PushTags(basic_task_info=basic_task_info).run()
        commit_changes_mock.assert_called_once_with(
            commit_message=f"Committing staged changes for {current_version}",
            project_root=basic_task_info.docker_project_root,
            local_uid=basic_task_info.local_uid,
            local_gid=basic_task_info.local_gid,
            local_user_env=basic_task_info.local_user_env,
        )
        tag_and_push_mock.assert_called_once_with(
            tag=current_version,
            project_root=basic_task_info.docker_project_root,
            local_uid=basic_task_info.local_uid,
            local_gid=basic_task_info.local_gid,
            local_user_env=basic_task_info.local_user_env,
        )


def test_push_pypi_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushPypi(basic_task_info=basic_task_info).required_tasks() == [
        PushTags(basic_task_info=basic_task_info),
        BuildPypi(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_push_pypi(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(func=PushPypi(basic_task_info=basic_task_info).run)
