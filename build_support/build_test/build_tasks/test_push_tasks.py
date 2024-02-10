from pathlib import Path
from unittest.mock import call, patch

import pytest
from build_tasks.build_tasks import BuildPypi
from build_tasks.push_tasks import PushAll, PushPypi, PushTags
from build_tasks.test_tasks import TestAll
from build_vars.git_status_vars import MAIN_BRANCH_NAME
from dag_engine import concatenate_args


def test_push_all_requires():
    assert PushAll().required_tasks() == [PushTags(), PushPypi()]


def test_run_push_all(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.push_tasks.run_process") as run_process_mock:
        PushAll().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 0


def test_push_tags_requires():
    assert PushTags().required_tasks() == [TestAll()]


@pytest.mark.parametrize(
    "branch_name, current_version",
    [
        (MAIN_BRANCH_NAME, "0.0.1-dev.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1"),
    ],
)
def test_run_push_tags_not_allowed(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
    branch_name: str,
    current_version: str,
):
    with patch("build_tasks.push_tasks.get_current_branch") as get_branch_mock, patch(
        "build_tasks.push_tasks.get_project_version"
    ) as get_version_mock, pytest.raises(ValueError):
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        PushTags().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )


@pytest.mark.parametrize(
    "branch_name, current_version",
    [
        (MAIN_BRANCH_NAME, "0.0.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1-dev.1"),
    ],
)
def test_run_push_tags_allowed_no_diff(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
    branch_name: str,
    current_version: str,
):
    with patch("build_tasks.push_tasks.run_process") as run_process_mock, patch(
        "build_tasks.push_tasks.get_git_diff"
    ) as get_git_diff_mock, patch(
        "build_tasks.push_tasks.get_current_branch"
    ) as get_branch_mock, patch(
        "build_tasks.push_tasks.get_project_version"
    ) as get_version_mock:
        get_git_diff_mock.return_value = ""
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        PushTags().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        git_tag_args = concatenate_args(args=["git", "tag", current_version])
        git_push_tags_args = concatenate_args(args=["git", "push", "--tags"])
        assert run_process_mock.call_count == 2
        run_process_mock.assert_has_calls(
            calls=[
                call(args=args, local_user_uid=local_uid, local_user_gid=local_gid)
                for args in [
                    git_tag_args,
                    git_push_tags_args,
                ]
            ]
        )


@pytest.mark.parametrize(
    "branch_name, current_version",
    [
        (MAIN_BRANCH_NAME, "0.0.1"),
        ("not_" + MAIN_BRANCH_NAME, "0.0.1-dev.1"),
    ],
)
def test_run_push_tags_allowed_with_diff(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
    branch_name: str,
    current_version: str,
):
    with patch("build_tasks.push_tasks.run_process") as run_process_mock, patch(
        "build_tasks.push_tasks.get_git_diff"
    ) as get_git_diff_mock, patch(
        "build_tasks.push_tasks.get_current_branch"
    ) as get_branch_mock, patch(
        "build_tasks.push_tasks.get_project_version"
    ) as get_version_mock:
        get_git_diff_mock.return_value = "some_diff"
        get_branch_mock.return_value = branch_name
        get_version_mock.return_value = current_version
        PushTags().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        git_add_args = concatenate_args(args=["git", "add", "-u"])
        git_commit_args = concatenate_args(
            args=[
                "git",
                "commit",
                "-m",
                f"'Committing staged changes for {current_version}'",
            ]
        )
        git_push_args = concatenate_args(args=["git", "push"])
        git_tag_args = concatenate_args(args=["git", "tag", current_version])
        git_push_tags_args = concatenate_args(args=["git", "push", "--tags"])
        assert run_process_mock.call_count == 5
        run_process_mock.assert_has_calls(
            calls=[
                call(args=args, local_user_uid=local_uid, local_user_gid=local_gid)
                for args in [
                    git_add_args,
                    git_commit_args,
                    git_push_args,
                    git_tag_args,
                    git_push_tags_args,
                ]
            ]
        )


def test_push_pypi_requires():
    assert PushPypi().required_tasks() == [PushTags(), BuildPypi()]


def test_run_push_pypi(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.push_tasks.run_process") as run_process_mock:
        PushPypi().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 0
