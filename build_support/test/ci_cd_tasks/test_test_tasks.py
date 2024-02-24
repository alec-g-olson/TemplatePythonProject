from pathlib import Path
from unittest.mock import call, patch

from build_support.ci_cd_tasks.env_setup_tasks import BuildDevEnvironment, GetGitInfo
from build_support.ci_cd_tasks.test_tasks import (
    TestAll,
    TestBuildSupport,
    TestPypi,
    TestPythonStyle,
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
    get_all_python_folders,
    get_all_src_folders,
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


def test_test_all_requires():
    assert TestAll().required_tasks() == [
        TestPypi(),
        TestBuildSupport(),
        TestPythonStyle(),
    ]


def test_run_test_all(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.test_tasks.run_process") as run_process_mock:
        TestAll().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 0


def test_test_build_support_requires():
    assert TestBuildSupport().required_tasks() == [GetGitInfo(), BuildDevEnvironment()]


def test_run_test_build_support(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.test_tasks.run_process") as run_process_mock:
        TestBuildSupport().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.BUILD_SUPPORT,
                ),
                get_build_support_src_and_test(project_root=docker_project_root),
            ]
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)


def test_test_python_style_requires():
    assert TestPythonStyle().required_tasks() == [GetGitInfo(), BuildDevEnvironment()]


def test_run_test_python_style(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.test_tasks.run_process") as run_process_mock:
        TestPythonStyle().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        test_isort_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "isort",
                "--check-only",
                get_all_python_folders(project_root=docker_project_root),
            ]
        )
        test_black_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "black",
                "--check",
                get_all_python_folders(project_root=docker_project_root),
            ]
        )
        test_pydocstyle_src_folders_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pydocstyle",
                get_all_src_folders(project_root=docker_project_root),
            ]
        )
        test_pydocstyle_test_folders_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pydocstyle",
                "--add-ignore=D100,D104",
                get_all_test_folders(project_root=docker_project_root),
            ]
        )
        test_documentation_enforcement_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
                ),
                get_documentation_tests_dir(project_root=docker_project_root),
            ]
        )
        test_flake8_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "flake8",
                get_all_python_folders(project_root=docker_project_root),
            ]
        )
        mypy_command = concatenate_args(
            args=[
                get_base_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "-e",
                get_mypy_path_env(
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                get_docker_image_name(
                    project_root=docker_project_root, target_image=DockerTarget.DEV
                ),
                "mypy",
                "--explicit-package-bases",
            ]
        )
        test_mypy_pypi_args = concatenate_args(
            args=[
                mypy_command,
                get_pypi_src_and_test(project_root=docker_project_root),
            ]
        )
        test_mypy_build_support_src_args = concatenate_args(
            args=[
                mypy_command,
                get_build_support_src_dir(project_root=docker_project_root),
            ]
        )
        test_mypy_build_support_test_args = concatenate_args(
            args=[
                mypy_command,
                get_build_support_test_dir(project_root=docker_project_root),
            ]
        )
        test_mypy_pulumi_args = concatenate_args(
            args=[
                mypy_command,
                get_pulumi_dir(project_root=docker_project_root),
            ]
        )
        test_bandit_pypi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.PYPI,
                ),
                "-r",
                get_pypi_src_dir(project_root=docker_project_root),
            ]
        )
        test_bandit_pulumi_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.PULUMI,
                ),
                "-r",
                get_pulumi_dir(project_root=docker_project_root),
            ]
        )
        test_bandit_build_support_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "bandit",
                "-o",
                get_bandit_report_path(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.BUILD_SUPPORT,
                ),
                "-r",
                get_build_support_src_dir(project_root=docker_project_root),
            ]
        )

        all_call_args = [
            test_isort_args,
            test_black_args,
            test_pydocstyle_src_folders_args,
            test_pydocstyle_test_folders_args,
            test_documentation_enforcement_args,
            test_flake8_args,
            test_mypy_pypi_args,
            test_mypy_build_support_src_args,
            test_mypy_build_support_test_args,
            test_mypy_pulumi_args,
            test_bandit_pypi_args,
            test_bandit_pulumi_args,
            test_bandit_build_support_args,
        ]
        run_process_mock.assert_has_calls(
            calls=[call(args=args) for args in all_call_args]
        )
        assert run_process_mock.call_count == len(all_call_args)


def test_test_pypi_requires():
    assert TestPypi().required_tasks() == [BuildDevEnvironment()]


def test_run_test_pypi(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.test_tasks.run_process") as run_process_mock:
        TestPypi().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        test_build_sanity_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "-n",
                THREADS_AVAILABLE,
                get_pytest_report_args(
                    project_root=docker_project_root,
                    test_context=SubprojectContext.PYPI,
                ),
                get_pypi_src_and_test(project_root=docker_project_root),
            ]
        )
        run_process_mock.assert_called_once_with(args=test_build_sanity_args)
