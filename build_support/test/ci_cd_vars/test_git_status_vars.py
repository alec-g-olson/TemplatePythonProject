import re
from unittest.mock import call, patch

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.git_status_vars import (
    MAIN_BRANCH_NAME,
    commit_changes_if_diff,
    current_branch_is_main,
    get_current_branch,
    get_git_diff,
    get_local_tags,
)
from build_support.dag_engine import concatenate_args


def test_get_current_branch() -> None:
    patch_branch_name = "some_branch_name"
    with patch(
        "build_support.ci_cd_vars.git_status_vars.get_output_of_process",
    ) as get_output_patch:
        get_output_patch.return_value = patch_branch_name
        assert get_current_branch() == patch_branch_name
        get_output_patch.assert_called_once_with(
            args=["git", "rev-parse", "--abbrev-ref", "HEAD"],
            user_uid=0,
            user_gid=0,
            silent=True,
        )


def test_get_current_branch_as_user() -> None:
    patch_branch_name = "some_branch_name"
    with patch(
        "build_support.ci_cd_vars.git_status_vars.get_output_of_process",
    ) as get_output_patch:
        get_output_patch.return_value = patch_branch_name
        assert (
            get_current_branch(local_user_uid=1337, local_user_gid=42)
            == patch_branch_name
        )
        get_output_patch.assert_called_once_with(
            args=["git", "rev-parse", "--abbrev-ref", "HEAD"],
            user_uid=1337,
            user_gid=42,
            silent=True,
        )


def test_constants_not_changed_by_accident() -> None:
    assert MAIN_BRANCH_NAME == "main"


def test_current_branch_is_main() -> None:
    assert current_branch_is_main(current_branch=MAIN_BRANCH_NAME)


def test_current_branch_is_not_main() -> None:
    assert not current_branch_is_main(current_branch="not_" + MAIN_BRANCH_NAME)


def test_get_local_tags() -> None:
    patch_tag_values = "v0.0.0\nv0.0.1\nv0.1.0\nv1.0.0"
    with patch(
        "build_support.ci_cd_vars.git_status_vars.get_output_of_process",
    ) as get_output_patch:
        get_output_patch.return_value = patch_tag_values
        assert get_local_tags() == ["v0.0.0", "v0.0.1", "v0.1.0", "v1.0.0"]
        get_output_patch.assert_called_once_with(
            args=["git", "tag"], user_uid=0, user_gid=0, silent=True
        )


def test_get_local_tags_as_user() -> None:
    patch_tag_values = "v0.0.0\nv0.0.1\nv0.1.0\nv1.0.0"
    with patch(
        "build_support.ci_cd_vars.git_status_vars.get_output_of_process",
    ) as get_output_patch:
        get_output_patch.return_value = patch_tag_values
        assert get_local_tags(local_user_uid=1337, local_user_gid=42) == [
            "v0.0.0",
            "v0.0.1",
            "v0.1.0",
            "v1.0.0",
        ]
        get_output_patch.assert_called_once_with(
            args=["git", "tag"], user_uid=1337, user_gid=42, silent=True
        )


def test_get_git_diff() -> None:
    patch_diff_result = "some_diff"
    with patch(
        "build_support.ci_cd_vars.git_status_vars.get_output_of_process",
    ) as get_output_patch:
        get_output_patch.return_value = patch_diff_result
        assert get_git_diff() == patch_diff_result
        get_output_patch.assert_called_once_with(args=["git", "diff"], silent=True)


@pytest.fixture(params=["Valid message!", "Hasn't got double quotes."])
def valid_commit_message(request: SubRequest) -> str:
    return request.param


def test_commit_changes_no_diff(
    valid_commit_message: str,
    local_uid: int,
    local_gid: int,
) -> None:
    with patch(
        "build_support.ci_cd_vars.git_status_vars.run_process",
    ) as run_process_mock, patch(
        "build_support.ci_cd_vars.git_status_vars.get_git_diff",
    ) as get_git_diff_mock:
        get_git_diff_mock.return_value = ""
        commit_changes_if_diff(
            commit_message_no_quotes=valid_commit_message,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 0


def test_commit_changes_bad_message(
    local_uid: int,
    local_gid: int,
) -> None:
    bad_message = 'A message with a double quote! (")'
    with patch(
        "build_support.ci_cd_vars.git_status_vars.run_process",
    ) as run_process_mock:
        expected_message = (
            "Commit message is not allowed to have double quotes. "
            f"commit_message_no_quotes='{bad_message}'"
        )
        with pytest.raises(ValueError, match=re.escape(expected_message)):
            commit_changes_if_diff(
                commit_message_no_quotes=bad_message,
                local_user_uid=local_uid,
                local_user_gid=local_gid,
            )
        assert run_process_mock.call_count == 0


def test_commit_changes_with_diff_on_main(
    valid_commit_message: str,
    local_uid: int,
    local_gid: int,
) -> None:
    branch_name = MAIN_BRANCH_NAME
    with patch(
        "build_support.ci_cd_vars.git_status_vars.run_process",
    ) as run_process_mock, patch(
        "build_support.ci_cd_vars.git_status_vars.get_git_diff",
    ) as get_git_diff_mock, patch(
        "build_support.ci_cd_vars.git_status_vars.get_current_branch",
    ) as get_branch_mock:
        get_git_diff_mock.return_value = "some_diff"
        get_branch_mock.return_value = branch_name
        expected_message = (
            f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
        )
        with pytest.raises(RuntimeError, match=expected_message):
            commit_changes_if_diff(
                commit_message_no_quotes=valid_commit_message,
                local_user_uid=local_uid,
                local_user_gid=local_gid,
            )
        assert run_process_mock.call_count == 0


def test_run_push_tags_allowed_with_diff_not_main(
    valid_commit_message: str,
    local_uid: int,
    local_gid: int,
) -> None:
    branch_name = "not_" + MAIN_BRANCH_NAME
    with patch(
        "build_support.ci_cd_vars.git_status_vars.run_process",
    ) as run_process_mock, patch(
        "build_support.ci_cd_vars.git_status_vars.get_git_diff",
    ) as get_git_diff_mock, patch(
        "build_support.ci_cd_vars.git_status_vars.get_current_branch",
    ) as get_branch_mock:
        get_git_diff_mock.return_value = "some_diff"
        get_branch_mock.return_value = branch_name
        commit_changes_if_diff(
            commit_message_no_quotes=valid_commit_message,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        git_add_args = concatenate_args(args=["git", "add", "-u"])
        git_commit_args = concatenate_args(
            args=[
                "git",
                "commit",
                "-m",
                f'"{valid_commit_message}"',
            ],
        )
        git_push_args = concatenate_args(args=["git", "push"])
        run_process_call_args = [
            git_add_args,
            git_commit_args,
            git_push_args,
        ]
        assert run_process_mock.call_count == len(run_process_call_args)
        run_process_mock.assert_has_calls(
            calls=[
                call(
                    args=args,
                    user_uid=local_uid,
                    user_gid=local_gid,
                )
                for args in run_process_call_args
            ],
        )
