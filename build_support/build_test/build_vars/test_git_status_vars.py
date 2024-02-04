from unittest.mock import patch

from build_vars.git_status_vars import get_current_branch, get_local_tags


def test_get_current_branch():
    patch_branch_name = "some_branch_name"
    with patch("build_vars.git_status_vars.get_output_of_process") as get_output_patch:
        get_output_patch.return_value = patch_branch_name
        assert get_current_branch() == patch_branch_name
        get_output_patch.assert_called_once_with(
            args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
        )


def test_get_local_tags():
    patch_tag_values = "v0.0.0\nv0.0.1\nv0.1.0\nv1.0.0"
    with patch("build_vars.git_status_vars.get_output_of_process") as get_output_patch:
        get_output_patch.return_value = patch_tag_values
        assert get_local_tags() == ["v0.0.0", "v0.0.1", "v0.1.0", "v1.0.0"]
        get_output_patch.assert_called_once_with(args=["git", "tag"], silent=True)
