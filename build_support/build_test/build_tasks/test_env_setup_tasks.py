from copy import copy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from build_tasks.env_setup_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    BuildPulumiEnvironment,
    Clean,
    GetGitInfo,
    GitInfo,
)
from build_vars.docker_vars import DockerTarget, get_docker_build_command
from build_vars.file_and_dir_path_vars import get_build_dir, get_git_info_yaml
from build_vars.project_setting_vars import get_pulumi_version
from conftest import mock_project_versions


def test_build_dev_env_requires():
    assert BuildDevEnvironment().required_tasks() == []


def test_run_build_dev_env(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.env_setup_tasks.run_process") as run_process_mock:
        build_dev_env_args = get_docker_build_command(
            project_root=docker_project_root, target_image=DockerTarget.DEV
        )
        BuildDevEnvironment().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(args=build_dev_env_args)


def test_build_prod_env_requires():
    assert BuildProdEnvironment().required_tasks() == []


def test_run_build_prod_env(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.env_setup_tasks.run_process") as run_process_mock:
        build_prod_env_args = get_docker_build_command(
            project_root=docker_project_root, target_image=DockerTarget.PROD
        )
        BuildProdEnvironment().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(args=build_prod_env_args)


def test_build_pulumi_env_requires():
    assert BuildPulumiEnvironment().required_tasks() == []


def test_run_build_pulumi_env(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    mock_docker_poetry_lock_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.env_setup_tasks.run_process") as run_process_mock:
        build_pulumi_env_args = get_docker_build_command(
            project_root=docker_project_root,
            target_image=DockerTarget.PULUMI,
            extra_args={
                "--build-arg": "PULUMI_VERSION="
                + get_pulumi_version(project_root=docker_project_root)
            },
        )
        BuildPulumiEnvironment().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(args=build_pulumi_env_args)


def test_clean_requires():
    assert Clean().required_tasks() == []


def test_run_clean(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.env_setup_tasks.run_process") as run_process_mock:
        clean_args = ["rm", "-rf", get_build_dir(project_root=docker_project_root)]
        Clean().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(args=clean_args)


git_info_data_dict: dict[Any, Any] = {
    "branch": "some_branch_name",
    "tags": mock_project_versions,
}


@pytest.fixture
def git_info_yaml_str() -> str:
    return yaml.dump(git_info_data_dict)


def test_load_git_info(git_info_yaml_str: str):
    git_info = GitInfo.from_yaml(git_info_yaml_str)
    assert git_info == GitInfo(**git_info_data_dict)


def test_load_git_info_bad_branch():
    bad_dict = copy(git_info_data_dict)
    bad_dict["branch"] = 4
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_load_git_info_bad_tags_not_list():
    bad_dict = copy(git_info_data_dict)
    bad_dict["tags"] = "0.0.0"
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_load_git_info_bad_tags_not_list_of_str():
    bad_dict = copy(git_info_data_dict)
    bad_dict["tags"] = [0, 1, "0.1.0"]
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_dump_git_info(git_info_yaml_str: str):
    git_info = GitInfo(**git_info_data_dict)
    assert git_info.to_yaml() == git_info_yaml_str


def test_get_git_info_requires():
    assert GetGitInfo().required_tasks() == []


def test_run_get_git_info(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_tasks.env_setup_tasks.run_process") as run_process_mock, patch(
        "build_tasks.env_setup_tasks.get_current_branch"
    ) as get_branch_mock, patch(
        "build_tasks.env_setup_tasks.get_local_tags"
    ) as get_tags_mock:
        get_fetch_args = ["git", "fetch"]
        branch_name = "some_branch"
        tags = ["some_non_version_tag", "0.0.0", "0.1.0"]
        get_branch_mock.return_value = branch_name
        get_tags_mock.return_value = tags
        git_info_yaml_dest = get_git_info_yaml(project_root=docker_project_root)
        assert not git_info_yaml_dest.exists()
        GetGitInfo().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        run_process_mock.assert_called_once_with(
            args=get_fetch_args,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        observed_git_info = GitInfo.from_yaml(git_info_yaml_dest.read_text())
        expected_git_info = GitInfo(branch=branch_name, tags=tags)
        assert observed_git_info == expected_git_info
