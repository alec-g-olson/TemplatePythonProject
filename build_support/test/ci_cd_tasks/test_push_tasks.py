from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.build_tasks import BuildPypi
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi, PushTags
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import ValidateAll
from build_support.ci_cd_vars.git_status_vars import MAIN_BRANCH_NAME
from build_support.process_runner import concatenate_args


def test_push_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushAll(basic_task_info=basic_task_info).required_tasks() == [
        PushTags(basic_task_info=basic_task_info),
        PushPypi(basic_task_info=basic_task_info),
    ]


def test_run_push_all(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.push_tasks.run_process") as run_process_mock:
        PushAll(basic_task_info=basic_task_info).run()
        assert run_process_mock.call_count == 0


def test_push_tags_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushTags(basic_task_info=basic_task_info).required_tasks() == [
        ValidateAll(basic_task_info=basic_task_info)
    ]


@pytest.mark.parametrize(
    ("branch_name", "current_version"),
    [
        (MAIN_BRANCH_NAME, "0.0.1-dev.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1"),
    ],
)
def test_run_push_tags_not_allowed(
    basic_task_info: BasicTaskInfo,
    branch_name: str,
    current_version: str,
) -> None:
    with (
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_current_branch",
        ) as get_branch_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_project_version",
        ) as get_version_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.run_process",
        ) as run_process_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.commit_changes_if_diff",
        ) as commit_changes_mock,
    ):
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        expected_message = (
            f"Tag {current_version} is incompatible with branch {branch_name}."
        )
        with pytest.raises(ValueError, match=expected_message):
            PushTags(basic_task_info=basic_task_info).run()
        run_process_mock.assert_not_called()
        commit_changes_mock.assert_not_called()


@pytest.mark.parametrize(
    ("branch_name", "current_version"),
    [
        (MAIN_BRANCH_NAME, "0.0.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1-dev.1"),
    ],
)
def test_run_push_tags_allowed(
    basic_task_info: BasicTaskInfo,
    branch_name: str,
    current_version: str,
) -> None:
    with (
        patch(
            "build_support.ci_cd_tasks.push_tasks.run_process",
        ) as run_process_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.commit_changes_if_diff",
        ) as commit_changes_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_current_branch",
        ) as get_branch_mock,
        patch(
            "build_support.ci_cd_tasks.push_tasks.get_project_version",
        ) as get_version_mock,
    ):
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        PushTags(basic_task_info=basic_task_info).run()
        git_tag_args = concatenate_args(args=["git", "tag", current_version])
        git_push_tags_args = concatenate_args(args=["git", "push", "--tags"])
        run_process_call_args = [
            git_tag_args,
            git_push_tags_args,
        ]
        assert run_process_mock.call_count == len(run_process_call_args)
        run_process_mock.assert_has_calls(
            calls=[
                call(
                    args=args,
                    user_uid=basic_task_info.local_user_uid,
                    user_gid=basic_task_info.local_user_gid,
                )
                for args in run_process_call_args
            ],
        )
        commit_changes_mock.assert_called_once_with(
            commit_message_no_quotes=(
                f"Committing staged changes for {current_version}"
            ),
            local_user_uid=basic_task_info.local_user_uid,
            local_user_gid=basic_task_info.local_user_gid,
        )


def test_push_pypi_requires(basic_task_info: BasicTaskInfo) -> None:
    assert PushPypi(basic_task_info=basic_task_info).required_tasks() == [
        PushTags(basic_task_info=basic_task_info),
        BuildPypi(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_push_pypi(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.push_tasks.run_process") as run_process_mock:
        PushPypi(basic_task_info=basic_task_info).run()
        assert run_process_mock.call_count == 0
