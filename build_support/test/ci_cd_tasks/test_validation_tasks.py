from pathlib import Path
from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
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
    get_build_support_src_and_test,
    get_build_support_src_dir,
    get_build_support_test_dir,
    get_documentation_tests_dir,
    get_pulumi_dir,
    get_pypi_src_and_test,
    get_pypi_src_dir,
)
from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE
from build_support.ci_cd_vars.python_vars import (
    get_bandit_report_path,
    get_pytest_report_args,
)
from build_support.dag_engine import concatenate_args


@pytest.fixture()
def validate_all_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> ValidateAll:
    return ValidateAll(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_validate_all_requires(validate_all_task: ValidateAll) -> None:
    assert validate_all_task.required_tasks() == [
        ValidatePypi(
            non_docker_project_root=validate_all_task.non_docker_project_root,
            docker_project_root=validate_all_task.docker_project_root,
            local_user_uid=validate_all_task.local_user_uid,
            local_user_gid=validate_all_task.local_user_gid,
        ),
        ValidateBuildSupport(
            non_docker_project_root=validate_all_task.non_docker_project_root,
            docker_project_root=validate_all_task.docker_project_root,
            local_user_uid=validate_all_task.local_user_uid,
            local_user_gid=validate_all_task.local_user_gid,
        ),
        ValidatePythonStyle(
            non_docker_project_root=validate_all_task.non_docker_project_root,
            docker_project_root=validate_all_task.docker_project_root,
            local_user_uid=validate_all_task.local_user_uid,
            local_user_gid=validate_all_task.local_user_gid,
        ),
    ]


def test_run_validate_all(validate_all_task: ValidateAll) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        validate_all_task.run()
        assert run_process_mock.call_count == 0


@pytest.fixture()
def validate_build_support_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> ValidateBuildSupport:
    return ValidateBuildSupport(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_validate_build_support_requires(
    validate_build_support_task: ValidateBuildSupport,
) -> None:
    assert validate_build_support_task.required_tasks() == [
        GetGitInfo(
            non_docker_project_root=validate_build_support_task.non_docker_project_root,
            docker_project_root=validate_build_support_task.docker_project_root,
            local_user_uid=validate_build_support_task.local_user_uid,
            local_user_gid=validate_build_support_task.local_user_gid,
        ),
        SetupDevEnvironment(
            non_docker_project_root=validate_build_support_task.non_docker_project_root,
            docker_project_root=validate_build_support_task.docker_project_root,
            local_user_uid=validate_build_support_task.local_user_uid,
            local_user_gid=validate_build_support_task.local_user_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_build_support(
    validate_build_support_task: ValidateBuildSupport,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        task = validate_build_support_task
        task.run()
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.BUILD_SUPPORT,
                ),
                get_build_support_src_and_test(
                    project_root=task.docker_project_root,
                ),
            ],
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)


@pytest.fixture()
def validate_python_style_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> ValidatePythonStyle:
    return ValidatePythonStyle(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_validate_python_style_requires(
    validate_python_style_task: ValidatePythonStyle,
) -> None:
    assert validate_python_style_task.required_tasks() == [
        GetGitInfo(
            non_docker_project_root=validate_python_style_task.non_docker_project_root,
            docker_project_root=validate_python_style_task.docker_project_root,
            local_user_uid=validate_python_style_task.local_user_uid,
            local_user_gid=validate_python_style_task.local_user_gid,
        ),
        SetupDevEnvironment(
            non_docker_project_root=validate_python_style_task.non_docker_project_root,
            docker_project_root=validate_python_style_task.docker_project_root,
            local_user_uid=validate_python_style_task.local_user_uid,
            local_user_gid=validate_python_style_task.local_user_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_python_style(
    validate_python_style_task: ValidatePythonStyle,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        task = validate_python_style_task
        task.run()
        ruff_check_src_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                get_all_non_test_folders(project_root=task.docker_project_root),
            ],
        )
        ruff_check_test_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "ruff",
                "check",
                "--ignore",
                "D",
                get_all_test_folders(project_root=task.docker_project_root),
            ],
        )
        test_documentation_enforcement_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
                ),
                get_documentation_tests_dir(project_root=task.docker_project_root),
            ],
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image_name(
                    project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "mypy",
                "--explicit-package-bases",
            ],
        )
        mypy_pypi_args = concatenate_args(
            args=[
                mypy_command,
                get_pypi_src_and_test(project_root=task.docker_project_root),
            ],
        )
        mypy_build_support_src_args = concatenate_args(
            args=[
                mypy_command,
                get_build_support_src_dir(project_root=task.docker_project_root),
            ],
        )
        mypy_build_support_test_args = concatenate_args(
            args=[
                mypy_command,
                get_build_support_test_dir(project_root=task.docker_project_root),
            ],
        )
        mypy_pulumi_args = concatenate_args(
            args=[
                mypy_command,
                get_pulumi_dir(project_root=task.docker_project_root),
            ],
        )
        bandit_pypi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.PYPI,
                ),
                "-r",
                get_pypi_src_dir(project_root=task.docker_project_root),
            ],
        )
        bandit_pulumi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.PULUMI,
                ),
                "-r",
                get_pulumi_dir(project_root=task.docker_project_root),
            ],
        )
        bandit_build_support_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.BUILD_SUPPORT,
                ),
                "-r",
                get_build_support_src_dir(project_root=task.docker_project_root),
            ],
        )
        all_call_args = [
            ruff_check_src_args,
            ruff_check_test_args,
            test_documentation_enforcement_args,
            mypy_pypi_args,
            mypy_build_support_src_args,
            mypy_build_support_test_args,
            mypy_pulumi_args,
            bandit_pypi_args,
            bandit_pulumi_args,
            bandit_build_support_args,
        ]
        run_process_mock.assert_has_calls(
            calls=[call(args=args) for args in all_call_args],
        )
        assert run_process_mock.call_count == len(all_call_args)


@pytest.fixture()
def validate_pypi_task(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> ValidatePypi:
    return ValidatePypi(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    )


def test_validate_pypi_requires(validate_pypi_task: ValidatePypi) -> None:
    task = validate_pypi_task
    assert task.required_tasks() == [
        SetupDevEnvironment(
            non_docker_project_root=task.non_docker_project_root,
            docker_project_root=task.docker_project_root,
            local_user_uid=task.local_user_uid,
            local_user_gid=task.local_user_gid,
        )
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_pypi(validate_pypi_task: ValidatePypi) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        task = validate_pypi_task
        task.run()
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=task.non_docker_project_root,
                    docker_project_root=task.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=task.docker_project_root,
                    test_context=SubprojectContext.PYPI,
                ),
                get_pypi_src_and_test(project_root=task.docker_project_root),
            ],
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)
