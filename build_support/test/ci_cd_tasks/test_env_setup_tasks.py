from copy import copy
from pathlib import Path
from typing import Any
from unittest.mock import call, patch

import pytest
import yaml
from conftest import mock_project_versions
from pydantic import ValidationError

from build_support.ci_cd_tasks.env_setup_tasks import (
    Clean,
    GetGitInfo,
    GitInfo,
    SetupDevEnvironment,
    SetupProdEnvironment,
    SetupPulumiEnvironment,
)
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_build_command
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_dir,
    get_git_info_yaml,
)
from build_support.ci_cd_vars.project_setting_vars import get_pulumi_version


def test_build_dev_env_requires(basic_task_info: BasicTaskInfo) -> None:
    assert SetupDevEnvironment(basic_task_info=basic_task_info).required_tasks() == []


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_dev_env(basic_task_info: BasicTaskInfo) -> None:
    with patch(
        "build_support.ci_cd_tasks.env_setup_tasks.run_process",
    ) as run_process_mock:
        build_dev_env_args = get_docker_build_command(
            project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        SetupDevEnvironment(basic_task_info=basic_task_info).run()
        run_process_mock.assert_called_once_with(args=build_dev_env_args)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_build_prod_env_requires(basic_task_info: BasicTaskInfo) -> None:
    assert SetupProdEnvironment(basic_task_info=basic_task_info).required_tasks() == []


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_prod_env(basic_task_info: BasicTaskInfo) -> None:
    with patch(
        "build_support.ci_cd_tasks.env_setup_tasks.run_process",
    ) as run_process_mock:
        build_prod_env_args = get_docker_build_command(
            project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.PROD,
        )
        SetupProdEnvironment(basic_task_info=basic_task_info).run()
        run_process_mock.assert_called_once_with(args=build_prod_env_args)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_build_pulumi_env_requires(basic_task_info: BasicTaskInfo) -> None:
    assert (
        SetupPulumiEnvironment(basic_task_info=basic_task_info).required_tasks() == []
    )


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_docker_poetry_lock_file"
)
def test_run_build_pulumi_env(basic_task_info: BasicTaskInfo) -> None:
    with patch(
        "build_support.ci_cd_tasks.env_setup_tasks.run_process",
    ) as run_process_mock:
        build_pulumi_env_args = get_docker_build_command(
            project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.PULUMI,
            extra_args={
                "--build-arg": "PULUMI_VERSION="
                + get_pulumi_version(project_root=basic_task_info.docker_project_root),
            },
        )
        SetupPulumiEnvironment(basic_task_info=basic_task_info).run()
        run_process_mock.assert_called_once_with(args=build_pulumi_env_args)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_clean_requires(basic_task_info: BasicTaskInfo) -> None:
    assert Clean(basic_task_info=basic_task_info).required_tasks() == []


def test_run_clean(basic_task_info: BasicTaskInfo) -> None:
    def _add_some_folders_and_files_to_folder(
        current_folder: Path,
        required_file_names: list[str] | None = None,
    ) -> None:
        current_folder.mkdir(parents=True, exist_ok=True)
        file_names_to_add = ["some.txt", "file.txt", "names.txt", "to.txt", "add.txt"]
        folder_names_to_add = ["some", "folder", "names", "to", "add"]
        if required_file_names:  # pragma: no cover - might be None
            file_names_to_add += required_file_names
        for file_name in file_names_to_add:
            current_folder.joinpath(file_name).touch()
        for folder_name in folder_names_to_add:
            new_folder = current_folder.joinpath(folder_name)
            new_folder.mkdir()
            new_folder.joinpath("some_folder_contents.txt").touch()

    mypy_cache = basic_task_info.docker_project_root.joinpath(".mypy_cache")
    _add_some_folders_and_files_to_folder(current_folder=mypy_cache)

    pytest_cache = basic_task_info.docker_project_root.joinpath(".pytest_cache")
    _add_some_folders_and_files_to_folder(current_folder=pytest_cache)

    ruff_cache = basic_task_info.docker_project_root.joinpath(".ruff_cache")
    _add_some_folders_and_files_to_folder(current_folder=ruff_cache)

    build_dir = get_build_dir(project_root=basic_task_info.docker_project_root)
    _add_some_folders_and_files_to_folder(current_folder=build_dir)

    folders_that_will_be_completely_removed = [
        mypy_cache,
        pytest_cache,
        ruff_cache,
        build_dir,
    ]

    for folder in folders_that_will_be_completely_removed:
        assert folder.exists()
        assert folder.is_dir()
        sub_folder_count = 0
        folder_file_count = 0
        for path in folder.glob("*"):
            if path.is_dir():
                sub_folder_count += 1
                assert len(list(path.glob("*"))) > 0
            else:
                folder_file_count += 1
        assert sub_folder_count > 0
        assert folder_file_count > 0

    Clean(basic_task_info=basic_task_info).run()
    for folder in folders_that_will_be_completely_removed:
        assert not folder.exists()


git_info_data_dict: dict[Any, Any] = {
    "branch": "some_branch_name",
    "tags": mock_project_versions,
}


@pytest.fixture()
def git_info_yaml_str() -> str:
    return yaml.dump(git_info_data_dict)


def test_load_git_info(git_info_yaml_str: str) -> None:
    git_info = GitInfo.from_yaml(git_info_yaml_str)
    assert git_info == GitInfo.model_validate(git_info_data_dict)


def test_load_git_info_bad_branch() -> None:
    bad_dict = copy(git_info_data_dict)
    bad_dict["branch"] = 4
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_load_git_info_bad_tags_not_list() -> None:
    bad_dict = copy(git_info_data_dict)
    bad_dict["tags"] = "0.0.0"
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_load_git_info_bad_tags_not_list_of_str() -> None:
    bad_dict = copy(git_info_data_dict)
    bad_dict["tags"] = [0, 1, "0.1.0"]
    git_info_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        GitInfo.from_yaml(git_info_yaml_str)


def test_dump_git_info(git_info_yaml_str: str) -> None:
    git_info = GitInfo.model_validate(git_info_data_dict)
    assert git_info.to_yaml() == git_info_yaml_str


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_get_git_info_requires(basic_task_info: BasicTaskInfo) -> None:
    assert GetGitInfo(basic_task_info=basic_task_info).required_tasks() == []


def test_run_get_git_info(basic_task_info: BasicTaskInfo) -> None:
    with (
        patch(
            "build_support.ci_cd_tasks.env_setup_tasks.run_process",
        ) as run_process_mock,
        patch(
            "build_support.ci_cd_tasks.env_setup_tasks.get_current_branch",
        ) as get_branch_mock,
        patch(
            "build_support.ci_cd_tasks.env_setup_tasks.get_local_tags",
        ) as get_tags_mock,
    ):
        branch_name = "some_branch"
        tags = ["some_non_version_tag", "0.0.0", "0.1.0"]
        get_branch_mock.return_value = branch_name
        get_tags_mock.return_value = tags
        git_info_yaml_dest = get_git_info_yaml(
            project_root=basic_task_info.docker_project_root
        )
        assert not git_info_yaml_dest.exists()
        GetGitInfo(basic_task_info=basic_task_info).run()
        expected_fix_permissions_call = call(
            args=[
                "chown",
                f"{basic_task_info.local_user_uid}:{basic_task_info.local_user_gid}",
                str(basic_task_info.docker_project_root),
            ]
        )
        expected_git_fetch_call = call(
            args=["git", "fetch"],
            user_uid=basic_task_info.local_user_uid,
            user_gid=basic_task_info.local_user_gid,
        )
        all_expected_calls = [expected_fix_permissions_call, expected_git_fetch_call]
        assert run_process_mock.call_count == len(all_expected_calls)
        run_process_mock.assert_has_calls(calls=all_expected_calls, any_order=True)
        observed_git_info = GitInfo.from_yaml(git_info_yaml_dest.read_text())
        expected_git_info = GitInfo(branch=branch_name, tags=tags)
        assert observed_git_info == expected_git_info
