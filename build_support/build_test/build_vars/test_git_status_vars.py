from unittest.mock import patch

from build_vars.git_status_vars import (
    MAIN_BRANCH_NAME,
    current_branch_is_main,
    get_current_branch,
    get_git_diff,
    get_local_tags,
)


def test_get_current_branch():
    patch_branch_name = "some_branch_name"
    with patch("build_vars.git_status_vars.get_output_of_process") as get_output_patch:
        get_output_patch.return_value = patch_branch_name
        assert get_current_branch() == patch_branch_name
        get_output_patch.assert_called_once_with(
            args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
        )


def test_constants_not_changed_by_accident():
    assert MAIN_BRANCH_NAME == "main"


def test_current_branch_is_main():
    assert current_branch_is_main(current_branch=MAIN_BRANCH_NAME)


def test_current_branch_is_not_main():
    assert not current_branch_is_main(current_branch="not_" + MAIN_BRANCH_NAME)


def test_get_local_tags():
    patch_tag_values = "v0.0.0\nv0.0.1\nv0.1.0\nv1.0.0"
    with patch("build_vars.git_status_vars.get_output_of_process") as get_output_patch:
        get_output_patch.return_value = patch_tag_values
        assert get_local_tags() == ["v0.0.0", "v0.0.1", "v0.1.0", "v1.0.0"]
        get_output_patch.assert_called_once_with(args=["git", "tag"], silent=True)


def test_get_git_diff():
    patch_diff_result = "some_diff"
    with patch("build_vars.git_status_vars.get_output_of_process") as get_output_patch:
        get_output_patch.return_value = patch_diff_result
        assert get_git_diff() == patch_diff_result
        get_output_patch.assert_called_once_with(args=["git", "diff"], silent=True)
