from pathlib import Path
from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.build_tasks import BuildPypi
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi, PushTags
from build_support.ci_cd_tasks.validation_tasks import ValidateAll
from build_support.ci_cd_vars.git_status_vars import MAIN_BRANCH_NAME
from build_support.dag_engine import concatenate_args


@pytest.fixture()
def push_all_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> PushAll:
    return PushAll(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_push_all_requires(push_all_task: PushAll) -> None:
    assert push_all_task.required_tasks() == [
        PushTags(
            non_docker_project_root=push_all_task.non_docker_project_root,
            docker_project_root=push_all_task.docker_project_root,
            local_user_uid=push_all_task.local_user_uid,
            local_user_gid=push_all_task.local_user_gid,
        ),
        PushPypi(
            non_docker_project_root=push_all_task.non_docker_project_root,
            docker_project_root=push_all_task.docker_project_root,
            local_user_uid=push_all_task.local_user_uid,
            local_user_gid=push_all_task.local_user_gid,
        ),
    ]


def test_run_push_all(push_all_task: PushAll) -> None:
    with patch("build_support.ci_cd_tasks.push_tasks.run_process") as run_process_mock:
        push_all_task.run()
        assert run_process_mock.call_count == 0


@pytest.fixture()
def push_tags_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> PushTags:
    return PushTags(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_push_tags_requires(push_tags_task: PushTags) -> None:
    assert push_tags_task.required_tasks() == [
        ValidateAll(
            non_docker_project_root=push_tags_task.non_docker_project_root,
            docker_project_root=push_tags_task.docker_project_root,
            local_user_uid=push_tags_task.local_user_uid,
            local_user_gid=push_tags_task.local_user_gid,
        )
    ]


@pytest.mark.parametrize(
    ("branch_name", "current_version"),
    [
        (MAIN_BRANCH_NAME, "0.0.1-dev.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1"),
    ],
)
def test_run_push_tags_not_allowed(
    push_tags_task: PushTags,
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
            push_tags_task.run()
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
    push_tags_task: PushTags,
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
        push_tags_task.run()
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
                    user_uid=push_tags_task.local_user_uid,
                    user_gid=push_tags_task.local_user_gid,
                )
                for args in run_process_call_args
            ],
        )
        commit_changes_mock.assert_called_once_with(
            commit_message_no_quotes=(
                f"Committing staged changes for {current_version}"
            ),
            local_user_uid=push_tags_task.local_user_uid,
            local_user_gid=push_tags_task.local_user_gid,
        )


@pytest.fixture()
def push_pypi_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> PushPypi:
    return PushPypi(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_push_pypi_requires(push_pypi_task: PushPypi) -> None:
    assert push_pypi_task.required_tasks() == [
        PushTags(
            non_docker_project_root=push_pypi_task.non_docker_project_root,
            docker_project_root=push_pypi_task.docker_project_root,
            local_user_uid=push_pypi_task.local_user_uid,
            local_user_gid=push_pypi_task.local_user_gid,
        ),
        BuildPypi(
            non_docker_project_root=push_pypi_task.non_docker_project_root,
            docker_project_root=push_pypi_task.docker_project_root,
            local_user_uid=push_pypi_task.local_user_uid,
            local_user_gid=push_pypi_task.local_user_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_push_pypi(push_pypi_task: PushPypi) -> None:
    with patch("build_support.ci_cd_tasks.push_tasks.run_process") as run_process_mock:
        push_pypi_task.run()
        assert run_process_mock.call_count == 0
