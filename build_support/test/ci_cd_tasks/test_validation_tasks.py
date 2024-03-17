from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import (
    ValidateAll,
    ValidateBuildSupport,
    ValidatePypi,
    ValidatePythonStyle,
)
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_base_docker_command_for_image,
    get_docker_command_for_image,
    get_docker_image_name,
    get_mypy_path_env,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    SubprojectContext,
    get_all_non_test_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE
from build_support.ci_cd_vars.subproject_structure import (
    get_all_python_subprojects_dict,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args


def test_validate_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidateAll(basic_task_info=basic_task_info).required_tasks() == [
        ValidatePypi(basic_task_info=basic_task_info),
        ValidateBuildSupport(basic_task_info=basic_task_info),
        ValidatePythonStyle(basic_task_info=basic_task_info),
    ]


def test_run_validate_all(basic_task_info: BasicTaskInfo) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        ValidateAll(basic_task_info=basic_task_info).run()
        assert run_process_mock.call_count == 0


def test_validate_build_support_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidateBuildSupport(basic_task_info=basic_task_info).required_tasks() == [
        GetGitInfo(basic_task_info=basic_task_info),
        SetupDevEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_build_support(basic_task_info: BasicTaskInfo) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        build_support_subproject = get_python_subproject(
            subproject_context=SubprojectContext.BUILD_SUPPORT,
            project_root=basic_task_info.docker_project_root,
        )
        ValidateBuildSupport(basic_task_info=basic_task_info).run()
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                build_support_subproject.get_pytest_report_args(),
                build_support_subproject.get_src_and_test_dir(),
            ],
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)


def test_validate_python_style_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidatePythonStyle(basic_task_info=basic_task_info).required_tasks() == [
        GetGitInfo(basic_task_info=basic_task_info),
        SetupDevEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_python_style(basic_task_info: BasicTaskInfo) -> None:
    subprojects = get_all_python_subprojects_dict(
        project_root=basic_task_info.docker_project_root
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        ValidatePythonStyle(basic_task_info=basic_task_info).run()
        ruff_check_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                get_all_non_test_folders(
                    project_root=basic_task_info.docker_project_root
                ),
            ],
        )
        ruff_check_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D,FBT",
                get_all_test_folders(project_root=basic_task_info.docker_project_root),
            ],
        )
        test_documentation_enforcement_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                subprojects[
                    SubprojectContext.DOCUMENTATION_ENFORCEMENT
                ].get_pytest_report_args(),
                subprojects[SubprojectContext.DOCUMENTATION_ENFORCEMENT].get_test_dir(),
            ],
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image_name(
                    project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "mypy",
                "--explicit-package-bases",
            ],
        )
        mypy_pypi_args = concatenate_args(
            args=[
                mypy_command,
                subprojects[SubprojectContext.PYPI].get_root_dir(),
            ],
        )
        mypy_build_support_src_args = concatenate_args(
            args=[
                mypy_command,
                subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
            ],
        )
        mypy_build_support_test_args = concatenate_args(
            args=[
                mypy_command,
                subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
            ],
        )
        mypy_process_and_style_enforcement_args = concatenate_args(
            args=[
                mypy_command,
                subprojects[SubprojectContext.DOCUMENTATION_ENFORCEMENT].get_root_dir(),
            ]
        )
        mypy_pulumi_args = concatenate_args(
            args=[
                mypy_command,
                subprojects[SubprojectContext.PULUMI].get_root_dir(),
            ],
        )
        bandit_pypi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                subprojects[SubprojectContext.PYPI].get_bandit_report_path(),
                "-r",
                subprojects[SubprojectContext.PYPI].get_src_dir(),
            ],
        )
        bandit_pulumi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                subprojects[SubprojectContext.PULUMI].get_bandit_report_path(),
                "-r",
                subprojects[SubprojectContext.PULUMI].get_src_dir(),
            ],
        )
        bandit_build_support_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                subprojects[SubprojectContext.BUILD_SUPPORT].get_bandit_report_path(),
                "-r",
                subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
            ],
        )
        all_call_args = [
            ruff_check_src_args,
            ruff_check_test_args,
            test_documentation_enforcement_args,
            mypy_pypi_args,
            mypy_build_support_src_args,
            mypy_build_support_test_args,
            mypy_process_and_style_enforcement_args,
            mypy_pulumi_args,
            bandit_pypi_args,
            bandit_pulumi_args,
            bandit_build_support_args,
        ]
        run_process_mock.assert_has_calls(
            calls=[call(args=args) for args in all_call_args],
        )
        assert run_process_mock.call_count == len(all_call_args)


def test_validate_pypi_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidatePypi(basic_task_info=basic_task_info).required_tasks() == [
        SetupDevEnvironment(basic_task_info=basic_task_info)
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_pypi(basic_task_info: BasicTaskInfo) -> None:
    pypi_subproject = get_python_subproject(
        subproject_context=SubprojectContext.PYPI,
        project_root=basic_task_info.docker_project_root,
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        ValidatePypi(basic_task_info=basic_task_info).run()
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                pypi_subproject.get_pytest_report_args(),
                pypi_subproject.get_src_and_test_dir(),
            ],
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)
