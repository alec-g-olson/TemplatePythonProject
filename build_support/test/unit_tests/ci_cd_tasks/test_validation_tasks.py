import re
import shutil
from pathlib import Path
from time import sleep
from typing import Any
from unittest.mock import call, patch

import pytest
from _pytest.fixtures import SubRequest
from junitparser import JUnitXml, TestCase, TestSuite
from test_utils.empty_function_check import is_an_empty_function
from tomlkit import TOMLDocument, document, parse, table

from build_support.ci_cd_tasks.env_setup_tasks import (
    GetGitInfo,
    GitInfo,
    SetupDevEnvironment,
)
from build_support.ci_cd_tasks.task_node import BasicTaskInfo, TaskNode
from build_support.ci_cd_tasks.validation_tasks import (
    FEATURE_TEST_FILE_NAME_REGEX,
    AllSubprojectFeatureTests,
    AllSubprojectSecurityChecks,
    AllSubprojectStaticTypeChecking,
    AllSubprojectUnitTests,
    EnforceProcess,
    SubprojectFeatureTests,
    SubprojectUnitTests,
    UnitTestInfo,
    ValidateAll,
    ValidatePythonStyle,
    ValidateSecurityChecks,
    ValidateStaticTypeChecking,
    get_subprojects_to_test,
)
from build_support.ci_cd_vars.build_paths import get_git_info_yaml
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_base_docker_command_for_image,
    get_docker_command_for_image,
    get_docker_image_name,
    get_mypy_path_env,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_test_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.machine_introspection_vars import THREADS_AVAILABLE
from build_support.ci_cd_vars.project_structure import get_feature_test_scratch_folder
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
    get_sorted_subproject_contexts,
)
from build_support.file_caching import CONFTEST_NAME, FileCacheEngine
from build_support.process_runner import concatenate_args


def test_validate_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidateAll(basic_task_info=basic_task_info).required_tasks() == [
        AllSubprojectUnitTests(basic_task_info=basic_task_info),
        ValidatePythonStyle(basic_task_info=basic_task_info),
        AllSubprojectStaticTypeChecking(basic_task_info=basic_task_info),
        AllSubprojectSecurityChecks(basic_task_info=basic_task_info),
        EnforceProcess(basic_task_info=basic_task_info),
        AllSubprojectFeatureTests(basic_task_info=basic_task_info),
    ]


def test_run_validate_all(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(func=ValidateAll(basic_task_info=basic_task_info).run)


def test_enforce_process_requires(basic_task_info: BasicTaskInfo) -> None:
    assert EnforceProcess(basic_task_info=basic_task_info).required_tasks() == [
        GetGitInfo(basic_task_info=basic_task_info),
        SetupDevEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_enforce_process(basic_task_info: BasicTaskInfo) -> None:
    build_support_subproject = get_python_subproject(
        subproject_context=SubprojectContext.BUILD_SUPPORT,
        project_root=basic_task_info.docker_project_root,
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        EnforceProcess(basic_task_info=basic_task_info).run()
        run_process_mock.assert_called_once_with(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=basic_task_info.non_docker_project_root,
                        docker_project_root=basic_task_info.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    build_support_subproject.get_pytest_whole_test_suite_report_args(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                    build_support_subproject.get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                ]
            )
        )


def test_all_subproject_static_type_checking_requires(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert AllSubprojectStaticTypeChecking(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        ValidateStaticTypeChecking(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_static_type_checking(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert is_an_empty_function(
        func=AllSubprojectStaticTypeChecking(basic_task_info=basic_task_info).run
    )


def test_validate_static_type_checking_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    assert ValidateStaticTypeChecking(
        basic_task_info=basic_task_info, subproject_context=subproject_context
    ).required_tasks() == [
        GetGitInfo(basic_task_info=basic_task_info),
        SetupDevEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_static_type_checking(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        ValidateStaticTypeChecking(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        run_process_mock.assert_called_once_with(
            args=concatenate_args(
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
                    mock_docker_subproject.get_root_dir(),
                ]
            )
        )


def test_all_subproject_security_checks_requires(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert AllSubprojectSecurityChecks(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        ValidateSecurityChecks(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_security_checks(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(
        func=AllSubprojectSecurityChecks(basic_task_info=basic_task_info).run
    )


def test_validate_security_checks_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    assert ValidateSecurityChecks(
        basic_task_info=basic_task_info, subproject_context=subproject_context
    ).required_tasks() == [
        GetGitInfo(basic_task_info=basic_task_info),
        SetupDevEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_validate_security_checks(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        ValidateSecurityChecks(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        run_process_mock.assert_called_once_with(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=basic_task_info.non_docker_project_root,
                        docker_project_root=basic_task_info.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "bandit",
                    "-o",
                    mock_docker_subproject.get_bandit_report_path(),
                    "-r",
                    mock_docker_subproject.get_src_dir(),
                ]
            )
        )


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
            ]
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
            ]
        )
        test_style_enforcement_args = concatenate_args(
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
                    SubprojectContext.BUILD_SUPPORT
                ].get_pytest_whole_test_suite_report_args(
                    test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                ),
                subprojects[SubprojectContext.BUILD_SUPPORT].get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                ),
            ]
        )
        all_call_args = [
            ruff_check_src_args,
            ruff_check_test_args,
            test_style_enforcement_args,
        ]
        run_process_mock.assert_has_calls(
            calls=[call(args=args) for args in all_call_args]
        )
        assert run_process_mock.call_count == len(all_call_args)


def test_all_subproject_unit_tests_requires(basic_task_info: BasicTaskInfo) -> None:
    assert AllSubprojectUnitTests(basic_task_info=basic_task_info).required_tasks() == [
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_unit_tests(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(
        func=AllSubprojectUnitTests(basic_task_info=basic_task_info).run
    )


def test_subproject_unit_tests_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    assert SubprojectUnitTests(
        basic_task_info=basic_task_info, subproject_context=subproject_context
    ).required_tasks() == [
        SetupDevEnvironment(basic_task_info=basic_task_info),
        GetGitInfo(basic_task_info=basic_task_info),
    ]


@pytest.fixture
def mock_entire_subproject(
    real_project_root_dir: Path,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    real_subproject = get_python_subproject(
        project_root=real_project_root_dir, subproject_context=subproject_context
    )
    real_root_dir = real_subproject.get_root_dir()
    test_root_dir = mock_docker_subproject.get_root_dir()
    shutil.copytree(src=real_root_dir, dst=test_root_dir)
    # rename python package dir
    read_package_name = real_subproject.get_python_package_dir().name
    copied_dir = mock_docker_subproject.get_src_dir().joinpath(read_package_name)
    shutil.move(src=copied_dir, dst=mock_docker_subproject.get_python_package_dir())


@pytest.fixture
def mock_git_info_yaml(
    docker_project_root: Path, subproject_context: SubprojectContext
) -> Path:
    """Creates a mock git_info.yaml file for use in testing."""
    git_info_yaml_path = get_git_info_yaml(project_root=docker_project_root)
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a GitInfo object with the subproject in the modified list
    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=[subproject_context],
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())
    return git_info_yaml_path


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_unit_tests_test_all(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        top_level_conftest = mock_docker_subproject.get_test_dir().joinpath(
            CONFTEST_NAME
        )
        top_level_conftest.parent.mkdir(parents=True, exist_ok=True)
        top_level_conftest.touch()
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_command = get_docker_command_for_image(
            non_docker_project_root=basic_task_info.non_docker_project_root,
            docker_project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        expected_run_process_calls = []
        for (
            src_file,
            test_file,
        ) in mock_docker_subproject.get_src_unit_test_file_pairs():
            src_module = SubprojectUnitTests.get_module_from_path(
                src_file_path=src_file, subproject=mock_docker_subproject
            )
            test_file_parent = test_file.parent
            test_file_name = test_file.stem
            coverage_config_path = mock_docker_subproject.get_build_dir().joinpath(
                f"coverage_config_{test_file_name}.toml"
            )
            expected_run_process_calls.append(
                call(
                    args=concatenate_args(
                        args=[
                            docker_command,
                            "pytest",
                            "-n",
                            THREADS_AVAILABLE,
                            "--cov-report",
                            "term-missing",
                            f"--cov={src_module}",
                            f"--cov={test_file_parent}",
                            f"--cov-config={coverage_config_path}",
                            test_file,
                        ]
                    )
                )
            )
        expected_run_process_calls.append(
            call(
                args=concatenate_args(
                    args=[
                        docker_command,
                        "pytest",
                        "-n",
                        THREADS_AVAILABLE,
                        mock_docker_subproject.get_pytest_whole_test_suite_report_args(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                        mock_docker_subproject.get_src_dir(),
                        mock_docker_subproject.get_test_suite_dir(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                    ]
                )
            )
        )
        assert run_process_mock.mock_calls == expected_run_process_calls


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_unit_tests_all_cached(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    cache_engine = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    for _, test_file in get_python_subproject(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    ).get_src_unit_test_file_pairs():
        cache_engine.update_test_pass_timestamp(file_path=test_file)
    cache_engine.write_text()
    # Everything above this line makes it so that there is unit test cache file
    # that has all files in it up to date.  This should make it so that no tests are
    # run
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        assert run_process_mock.call_count == 0


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_unit_tests_all_cached_but_top_test_conftest_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    cache_engine = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    for _, test_file in mock_docker_subproject.get_src_unit_test_file_pairs():
        cache_engine.update_test_pass_timestamp(file_path=test_file)
    cache_engine.write_text()
    sleep(1 / 1000)  # sleep just long enough for a new timestamp when writing file
    mock_docker_subproject.get_test_dir().joinpath(CONFTEST_NAME).write_text(
        "Updated Top Level Conftest"
    )
    # Everything above this line makes it so that there is unit test cache file
    # that has all files in it up to date, but then update the top level conftest in the
    # test folder.  This should make it so that all tests are run
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_command = get_docker_command_for_image(
            non_docker_project_root=basic_task_info.non_docker_project_root,
            docker_project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        expected_run_process_calls = []

        for (
            src_file,
            test_file,
        ) in mock_docker_subproject.get_src_unit_test_file_pairs():
            src_module = SubprojectUnitTests.get_module_from_path(
                src_file_path=src_file, subproject=mock_docker_subproject
            )
            test_file_parent = test_file.parent
            test_file_name = test_file.stem
            coverage_config_path = mock_docker_subproject.get_build_dir().joinpath(
                f"coverage_config_{test_file_name}.toml"
            )
            expected_run_process_calls.append(
                call(
                    args=concatenate_args(
                        args=[
                            docker_command,
                            "pytest",
                            "-n",
                            THREADS_AVAILABLE,
                            "--cov-report",
                            "term-missing",
                            f"--cov={src_module}",
                            f"--cov={test_file_parent}",
                            f"--cov-config={coverage_config_path}",
                            test_file,
                        ]
                    )
                )
            )
        expected_run_process_calls.append(
            call(
                args=concatenate_args(
                    args=[
                        docker_command,
                        "pytest",
                        "-n",
                        THREADS_AVAILABLE,
                        mock_docker_subproject.get_pytest_whole_test_suite_report_args(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                        mock_docker_subproject.get_src_dir(),
                        mock_docker_subproject.get_test_suite_dir(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                    ]
                )
            )
        )
        assert run_process_mock.mock_calls == expected_run_process_calls


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "mock_git_info_yaml")
def test_missing_test_file_for_src(
    mock_project_root: Path, docker_project_root: Path
) -> None:
    subproject_context = SubprojectContext.PYPI
    subproject = PythonSubproject(
        project_root=docker_project_root, subproject_context=subproject_context
    )
    file_name = "file.py"
    pypi_package_dir = subproject.get_python_package_dir()
    pypi_package_dir.mkdir(parents=True)
    pypi_package_dir.joinpath(file_name).touch()
    unit_test_folder = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    unit_test_folder.mkdir(parents=True)
    missing_test_file = unit_test_folder.joinpath(f"test_{file_name}")
    expected_msg = f"Expected {missing_test_file} to exist!"
    basic_task_info = BasicTaskInfo(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_uid=0,
        local_gid=0,
        local_user_env=None,
    )

    # Mock get_subprojects_to_test to return the subproject so the test actually runs
    with (
        patch(
            "build_support.ci_cd_tasks.validation_tasks.get_subprojects_to_test",
            return_value=[subproject_context],
        ),
        pytest.raises(ValueError, match=expected_msg),
    ):
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_unit_tests_some_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    expected_run_process_calls = []
    docker_command = get_docker_command_for_image(
        non_docker_project_root=basic_task_info.non_docker_project_root,
        docker_project_root=basic_task_info.docker_project_root,
        target_image=DockerTarget.DEV,
    )
    cache_both_src_and_test = 0
    cache_src = 1
    cache_test = 2
    files_to_update = []
    for file_index, (src_file, test_file) in enumerate(
        mock_docker_subproject.get_src_unit_test_file_pairs()
    ):
        src_module = SubprojectUnitTests.get_module_from_path(
            src_file_path=src_file, subproject=mock_docker_subproject
        )
        test_file_parent = test_file.parent
        test_file_name = test_file.stem
        coverage_config_path = mock_docker_subproject.get_build_dir().joinpath(
            f"coverage_config_{test_file_name}.toml"
        )
        run_process_call = call(
            args=concatenate_args(
                args=[
                    docker_command,
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    "--cov-report",
                    "term-missing",
                    f"--cov={src_module}",
                    f"--cov={test_file_parent}",
                    f"--cov-config={coverage_config_path}",
                    test_file,
                ]
            )
        )
        mod_ten = file_index % 10
        if mod_ten == cache_both_src_and_test:
            # Tests ran and neither src nor test are updated
            file_cache.update_test_pass_timestamp(file_path=test_file)
        elif mod_ten == cache_src:
            # Tests ran, but src was updated
            file_cache.update_test_pass_timestamp(file_path=test_file)
            files_to_update.append(src_file)
            expected_run_process_calls.append(run_process_call)
        elif mod_ten == cache_test:
            # Tests ran, but tests was updated
            file_cache.update_test_pass_timestamp(file_path=test_file)
            files_to_update.append(test_file)
            expected_run_process_calls.append(run_process_call)
        else:
            expected_run_process_calls.append(run_process_call)
    file_cache.write_text()
    sleep(1 / 1000)  # sleep just long enough for a new timestamp when writing file
    for file_to_update in files_to_update:
        file_to_update.write_text("Updated File")
    # This is needed for now because INFRA only has one file and therefore
    # skipping it skips the report generating test as well
    if expected_run_process_calls:
        expected_run_process_calls.append(
            call(
                args=concatenate_args(
                    args=[
                        docker_command,
                        "pytest",
                        "-n",
                        THREADS_AVAILABLE,
                        mock_docker_subproject.get_pytest_whole_test_suite_report_args(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                        mock_docker_subproject.get_src_dir(),
                        mock_docker_subproject.get_test_suite_dir(
                            test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                        ),
                    ]
                )
            )
        )
    # Everything above this line makes it so that there is unit test cache file
    # that has some, not all, files in it up to date.  This includes some src files
    # without their corresponding test file and vice versa, as well as some src and test
    # file pairs.  This will run tests on most files, but skip some.
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        assert run_process_mock.mock_calls == expected_run_process_calls


def test_all_subproject_feature_tests_requires(basic_task_info: BasicTaskInfo) -> None:
    assert AllSubprojectFeatureTests(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_feature_tests(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(
        func=AllSubprojectFeatureTests(basic_task_info=basic_task_info).run
    )


def test_subproject_feature_tests_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    expected_required_tasks: list[TaskNode] = [
        GetGitInfo(basic_task_info=basic_task_info),
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ),
    ]
    if subproject_context == SubprojectContext.BUILD_SUPPORT:
        expected_required_tasks.extend(
            [
                ValidatePythonStyle(basic_task_info=basic_task_info),
                EnforceProcess(basic_task_info=basic_task_info),
            ]
        )
    assert (
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks()
        == expected_required_tasks
    )


REPORT_XML_REGEX = re.compile(r"--junitxml=(.+)")


def run_feature_test_side_effect(args: list[Any]) -> None:
    test_file_name = Path(args[0]).name
    for arg in args:  # pragma: no cov - should always end early
        regex_match = REPORT_XML_REGEX.match(arg)
        if regex_match:
            path = Path(regex_match[1])
            case = TestCase(name=test_file_name)
            suite_name = f"suite_{test_file_name}"
            # allow for untyped calls to library
            suite = TestSuite(name=suite_name)  # type: ignore[no-untyped-call]
            suite.add_testcase(case)
            xml = JUnitXml()  # type: ignore[no-untyped-call]
            xml.add_testsuite(suite)
            xml.write(str(path))
            break


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_test_all(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process",
        side_effect=run_feature_test_side_effect,
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_project_root = basic_task_info.docker_project_root
        non_docker_project_root = basic_task_info.non_docker_project_root
        test_files = [
            file
            for file in mock_docker_subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
            ).glob("*")
            if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
        ]
        expected_calls = [
            call(
                args=concatenate_args(
                    args=[
                        get_docker_command_for_image(
                            non_docker_project_root=non_docker_project_root,
                            docker_project_root=docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "pytest",
                        "--basetemp",
                        get_feature_test_scratch_folder(
                            project_root=docker_project_root
                        ),
                        mock_docker_subproject.get_pytest_feature_test_report_args(),
                        test_file,
                    ]
                )
            )
            for test_file in test_files
        ]
        if len(expected_calls) > 0:
            assert run_process_mock.mock_calls == expected_calls
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_in_ci_cd_int_test_mode(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    basic_task_info.ci_cd_feature_test_mode = True
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process",
        side_effect=run_feature_test_side_effect,
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_project_root = basic_task_info.docker_project_root
        non_docker_project_root = basic_task_info.non_docker_project_root
        test_files = [
            file
            for file in mock_docker_subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
            ).glob("*")
            if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
        ]
        expected_calls = [
            call(
                args=concatenate_args(
                    args=[
                        get_docker_command_for_image(
                            non_docker_project_root=non_docker_project_root,
                            docker_project_root=docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "pytest",
                        "--basetemp",
                        get_feature_test_scratch_folder(
                            project_root=docker_project_root
                        ),
                        mock_docker_subproject.get_pytest_feature_test_report_args(),
                        test_file,
                    ]
                )
            )
            for test_file in test_files
        ]
        if subproject_context == SubprojectContext.BUILD_SUPPORT:
            run_process_mock.assert_not_called()
        else:
            assert run_process_mock.mock_calls == expected_calls


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_all_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    test_files = [
        file
        for file in mock_docker_subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        ).glob("*")
        if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
    ]
    for test_file in test_files:
        file_cache.update_test_pass_timestamp(file_path=test_file)
    file_cache.write_text()
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        run_process_mock.assert_not_called()


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_all_cached_but_top_test_conftest_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    test_files = [
        file
        for file in mock_docker_subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        ).glob("*")
        if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
    ]
    for test_file in test_files:
        file_cache.update_test_pass_timestamp(file_path=test_file)
    file_cache.write_text()
    sleep(1 / 1000)  # sleep just long enough for a new timestamp when writing file
    mock_docker_subproject.get_test_dir().joinpath(CONFTEST_NAME).write_text(
        "Updated Top Level Conftest"
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process",
        side_effect=run_feature_test_side_effect,
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_project_root = basic_task_info.docker_project_root
        non_docker_project_root = basic_task_info.non_docker_project_root
        expected_calls = [
            call(
                args=concatenate_args(
                    args=[
                        get_docker_command_for_image(
                            non_docker_project_root=non_docker_project_root,
                            docker_project_root=docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "pytest",
                        "--basetemp",
                        get_feature_test_scratch_folder(
                            project_root=docker_project_root
                        ),
                        mock_docker_subproject.get_pytest_feature_test_report_args(),
                        test_file,
                    ]
                )
            )
            for test_file in test_files
        ]
        if len(expected_calls) > 0:
            assert run_process_mock.mock_calls == expected_calls
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_some_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    test_files = [
        file
        for file in mock_docker_subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        ).glob("*")
        if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
    ]
    if len(test_files) <= 1:  # pragma: no cov - might not be true
        return
    test_files_to_run = []
    for index, test_file in enumerate(test_files):
        if index % 2 == 0:
            file_cache.update_test_pass_timestamp(file_path=test_file)
        else:
            test_files_to_run.append(test_file)
    file_cache.write_text()

    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process",
        side_effect=run_feature_test_side_effect,
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_project_root = basic_task_info.docker_project_root
        non_docker_project_root = basic_task_info.non_docker_project_root
        expected_calls = [
            call(
                args=concatenate_args(
                    args=[
                        get_docker_command_for_image(
                            non_docker_project_root=non_docker_project_root,
                            docker_project_root=docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "pytest",
                        "--basetemp",
                        get_feature_test_scratch_folder(
                            project_root=docker_project_root
                        ),
                        mock_docker_subproject.get_pytest_feature_test_report_args(),
                        test_file_to_run,
                    ]
                )
            )
            for test_file_to_run in test_files_to_run
        ]
        run_process_mock.assert_has_calls(calls=expected_calls)


@pytest.mark.usefixtures(
    "mock_docker_pyproject_toml_file", "mock_entire_subproject", "mock_git_info_yaml"
)
def test_run_subproject_feature_tests_one_src_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    test_files = [
        file
        for file in mock_docker_subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
        ).glob("*")
        if FEATURE_TEST_FILE_NAME_REGEX.match(file.name)
    ]
    for test_file in test_files:
        file_cache.update_test_pass_timestamp(file_path=test_file)
    file_cache.write_text()
    sleep(1 / 1000)  # sleep just long enough for a new timestamp when writing file
    src_file = next(mock_docker_subproject.get_all_testable_src_files())
    src_content = src_file.read_text()
    src_file.write_text(src_content + "\n")

    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process",
        side_effect=run_feature_test_side_effect,
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        docker_project_root = basic_task_info.docker_project_root
        non_docker_project_root = basic_task_info.non_docker_project_root
        expected_calls = [
            call(
                args=concatenate_args(
                    args=[
                        get_docker_command_for_image(
                            non_docker_project_root=non_docker_project_root,
                            docker_project_root=docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "pytest",
                        "--basetemp",
                        get_feature_test_scratch_folder(
                            project_root=docker_project_root
                        ),
                        mock_docker_subproject.get_pytest_feature_test_report_args(),
                        test_file,
                    ]
                )
            )
            for test_file in test_files
        ]
        if len(expected_calls) > 0:
            run_process_mock.assert_has_calls(calls=expected_calls)
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()


def test_get_subprojects_to_test_dockerfile_modified(docker_project_root: Path) -> None:
    """Test get_subprojects_to_test when dockerfile is modified."""
    git_info_yaml_path = get_git_info_yaml(project_root=docker_project_root)
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a GitInfo object with dockerfile modified
    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=[SubprojectContext.PYPI],
        dockerfile_modified=True,
        poetry_lock_file_modified=False,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())

    result = get_subprojects_to_test(project_root=docker_project_root)
    assert result == get_sorted_subproject_contexts()


def test_get_subprojects_to_test_poetry_lock_modified(
    docker_project_root: Path,
) -> None:
    """Test get_subprojects_to_test when poetry.lock is modified."""
    git_info_yaml_path = get_git_info_yaml(project_root=docker_project_root)
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a GitInfo object with poetry lock modified
    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=[SubprojectContext.PYPI],
        dockerfile_modified=False,
        poetry_lock_file_modified=True,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())

    result = get_subprojects_to_test(project_root=docker_project_root)
    assert result == get_sorted_subproject_contexts()


def test_get_subprojects_to_test_only_modified_subprojects(
    docker_project_root: Path,
) -> None:
    """Test get_subprojects_to_test when only specific subprojects are modified."""
    git_info_yaml_path = get_git_info_yaml(project_root=docker_project_root)
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a GitInfo object with only specific subprojects modified
    modified_subprojects = [SubprojectContext.PYPI, SubprojectContext.BUILD_SUPPORT]
    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=modified_subprojects,
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())

    result = get_subprojects_to_test(project_root=docker_project_root)
    assert result == modified_subprojects


def test_subproject_feature_tests_skips_when_not_in_test_list(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    """Test that SubprojectFeatureTests skips when subproject is not in test list."""
    # Create a git_info.yaml that doesn't include the current subproject
    other_subprojects = [
        ctx for ctx in get_sorted_subproject_contexts() if ctx != subproject_context
    ]
    git_info_yaml_path = get_git_info_yaml(
        project_root=basic_task_info.docker_project_root
    )
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=other_subprojects,
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())

    # The test should return early without running any processes
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        # Should not call run_process at all since we return early
        run_process_mock.assert_not_called()


def test_subproject_unit_tests_skips_when_not_in_test_list(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    """Test that SubprojectUnitTests skips when subproject is not in test list."""
    # Create a git_info.yaml that doesn't include the current subproject
    other_subprojects = [
        ctx for ctx in get_sorted_subproject_contexts() if ctx != subproject_context
    ]
    git_info_yaml_path = get_git_info_yaml(
        project_root=basic_task_info.docker_project_root
    )
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    git_info = GitInfo(
        branch="test-branch",
        tags=[],
        modified_subprojects=other_subprojects,
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )

    git_info_yaml_path.write_text(git_info.to_yaml())

    # The test should return early without running any processes
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        # Should not call run_process at all since we return early
        run_process_mock.assert_not_called()


# Test fixtures for different coverage settings
def _create_coverage_settings_basic() -> TOMLDocument:
    """Basic coverage settings with only run and report sections."""
    settings = document()
    settings["run"] = table()
    settings["run"]["branch"] = True
    settings["run"]["parallel"] = True
    settings["run"]["concurrency"] = ["multiprocessing", "thread"]
    settings["report"] = table()
    settings["report"]["fail_under"] = 100
    settings["report"]["exclude_lines"] = ["pragma: no cov"]
    return settings


def _create_coverage_settings_with_existing_omit() -> TOMLDocument:
    """Coverage settings with an existing omit list in run section."""
    settings = document()
    settings["run"] = table()
    settings["run"]["branch"] = True
    settings["run"]["parallel"] = True
    settings["run"]["concurrency"] = ["multiprocessing", "thread"]
    settings["run"]["omit"] = ["existing_file.py", "another_file.py"]
    settings["report"] = table()
    settings["report"]["fail_under"] = 100
    settings["report"]["exclude_lines"] = ["pragma: no cov"]
    return settings


def _create_coverage_settings_only_run() -> TOMLDocument:
    """Coverage settings with only run section."""
    settings = document()
    settings["run"] = table()
    settings["run"]["branch"] = True
    settings["run"]["parallel"] = True
    return settings


def _create_coverage_settings_only_report() -> TOMLDocument:
    """Coverage settings with only report section."""
    settings = document()
    settings["report"] = table()
    settings["report"]["fail_under"] = 100
    settings["report"]["exclude_lines"] = ["pragma: no cov"]
    return settings


def _create_coverage_settings_minimal() -> TOMLDocument:
    """Minimal coverage settings with no sections."""
    return document()


@pytest.fixture(
    params=[
        ("basic", _create_coverage_settings_basic),
        ("with_existing_omit", _create_coverage_settings_with_existing_omit),
        ("only_run", _create_coverage_settings_only_run),
        ("only_report", _create_coverage_settings_only_report),
        ("minimal", _create_coverage_settings_minimal),
    ],
    ids=["basic", "with_existing_omit", "only_run", "only_report", "minimal"],
)
def coverage_settings(request: SubRequest) -> tuple[str, TOMLDocument]:
    """Parameterized fixture providing different coverage settings configurations.

    Returns:
        tuple[str, TOMLDocument]: A tuple of (setting_type, settings_document)
    """
    setting_type, factory_func = request.param
    return (setting_type, factory_func())


# Factory functions for different test file setups
def _create_test_setup_single_file(
    subproject: PythonSubproject, docker_project_root: Path
) -> tuple[UnitTestInfo, Path, dict[str, Any]]:
    """Create a test setup with a single test file."""
    test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    ).joinpath("test_module")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir.joinpath("test_target.py")
    test_file.write_text("# test file")

    unit_test_info = UnitTestInfo(
        src_file_path=subproject.get_src_dir().joinpath("module.py"),
        test_file_path=test_file,
    )

    test_dir_relative = test_dir.relative_to(docker_project_root)
    expected_omit_patterns = [
        f"{test_dir_relative}/*/test_*.py",
        f"{test_dir_relative}/**/__init__.py",
        f"{test_dir_relative}/**/conftest.py",
    ]

    return (
        unit_test_info,
        test_dir,
        {
            "expected_omit_patterns": expected_omit_patterns,
            "expected_other_test_files": [],
        },
    )


def _create_test_setup_multiple_files(
    subproject: PythonSubproject, docker_project_root: Path
) -> tuple[UnitTestInfo, Path, dict[str, Any]]:
    """Create a test setup with multiple test files in the same directory."""
    test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    ).joinpath("test_module")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_target = test_dir.joinpath("test_target.py")
    test_target.write_text("# target test file")
    test_other1 = test_dir.joinpath("test_other1.py")
    test_other1.write_text("# other test file 1")
    test_other2 = test_dir.joinpath("test_other2.py")
    test_other2.write_text("# other test file 2")

    unit_test_info = UnitTestInfo(
        src_file_path=subproject.get_src_dir().joinpath("module.py"),
        test_file_path=test_target,
    )

    test_dir_relative = test_dir.relative_to(docker_project_root)
    expected_omit_patterns = [
        str(test_dir_relative.joinpath("test_other1.py")),
        str(test_dir_relative.joinpath("test_other2.py")),
        f"{test_dir_relative}/*/test_*.py",
        f"{test_dir_relative}/**/__init__.py",
        f"{test_dir_relative}/**/conftest.py",
    ]

    return (
        unit_test_info,
        test_dir,
        {
            "expected_omit_patterns": expected_omit_patterns,
            "expected_other_test_files": ["test_other1.py", "test_other2.py"],
        },
    )


def _create_test_setup_with_subdirs(
    subproject: PythonSubproject, docker_project_root: Path
) -> tuple[UnitTestInfo, Path, dict[str, Any]]:
    """Create a test setup with subdirectories containing test files."""
    test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    ).joinpath("test_module")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir.joinpath("test_target.py")
    test_file.write_text("# test file")

    # Create subdirectories with test files
    subdir1 = test_dir.joinpath("subdir1")
    subdir1.mkdir()
    subdir1.joinpath("test_sub1.py").write_text("# sub test")
    subdir2 = test_dir.joinpath("subdir2")
    subdir2.mkdir()
    subdir2.joinpath("test_sub2.py").write_text("# sub test")

    unit_test_info = UnitTestInfo(
        src_file_path=subproject.get_src_dir().joinpath("module.py"),
        test_file_path=test_file,
    )

    test_dir_relative = test_dir.relative_to(docker_project_root)
    expected_omit_patterns = [
        f"{test_dir_relative}/*/test_*.py",
        f"{test_dir_relative}/**/__init__.py",
        f"{test_dir_relative}/**/conftest.py",
    ]

    return (
        unit_test_info,
        test_dir,
        {
            "expected_omit_patterns": expected_omit_patterns,
            "expected_other_test_files": [],
            "has_subdirectories": True,
        },
    )


def _create_test_setup_complex(
    subproject: PythonSubproject, docker_project_root: Path
) -> tuple[UnitTestInfo, Path, dict[str, Any]]:
    """Create a complex test setup with multiple files and subdirectories."""
    test_dir = subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    ).joinpath("test_module")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create multiple test files
    test_target = test_dir.joinpath("test_target.py")
    test_target.write_text("# target")
    test_other1 = test_dir.joinpath("test_other1.py")
    test_other1.write_text("# other 1")
    test_other2 = test_dir.joinpath("test_other2.py")
    test_other2.write_text("# other 2")

    # Create subdirectories
    subdir = test_dir.joinpath("subdir")
    subdir.mkdir()
    subdir.joinpath("__init__.py").write_text("# init")
    subdir.joinpath("conftest.py").write_text("# conftest")
    subdir.joinpath("test_sub.py").write_text("# sub test")

    unit_test_info = UnitTestInfo(
        src_file_path=subproject.get_src_dir().joinpath("module.py"),
        test_file_path=test_target,
    )

    test_dir_relative = test_dir.relative_to(docker_project_root)
    expected_omit_patterns = [
        str(test_dir_relative.joinpath("test_other1.py")),
        str(test_dir_relative.joinpath("test_other2.py")),
        f"{test_dir_relative}/*/test_*.py",
        f"{test_dir_relative}/**/__init__.py",
        f"{test_dir_relative}/**/conftest.py",
    ]

    return (
        unit_test_info,
        test_dir,
        {
            "expected_omit_patterns": expected_omit_patterns,
            "expected_other_test_files": ["test_other1.py", "test_other2.py"],
            "has_subdirectories": True,
            "has_init_and_conftest": True,
        },
    )


@pytest.fixture(
    params=[
        ("single_file", _create_test_setup_single_file),
        ("multiple_files", _create_test_setup_multiple_files),
        ("with_subdirs", _create_test_setup_with_subdirs),
        ("complex", _create_test_setup_complex),
    ],
    ids=["single_file", "multiple_files", "with_subdirs", "complex"],
)
def test_file_setup(
    request: SubRequest, docker_project_root: Path
) -> tuple[str, UnitTestInfo, Path, dict[str, Any]]:
    """Parameterized fixture providing different test file setup configurations.

    Returns:
        tuple[str, UnitTestInfo, Path, dict[str, Any]]: A tuple of
        (setup_type, unit_test_info, test_dir, validation_info)
    """
    setup_type, factory_func = request.param
    subproject = get_python_subproject(
        subproject_context=SubprojectContext.BUILD_SUPPORT,
        project_root=docker_project_root,
    )
    unit_test_info, test_dir, validation_info = factory_func(
        subproject, docker_project_root
    )
    return (setup_type, unit_test_info, test_dir, validation_info)


# Helper functions for test evaluation
def _verify_omit_list_content(
    omit_list: list[str],
    setup_type: str,
    test_dir: Path,
    docker_project_root: Path,
    validation_info: dict[str, Any],
    original_omit_entries: list[str] | None = None,
) -> None:
    """Verify omit list contains expected patterns based on setup type.

    Args:
        omit_list: The omit list to verify
        setup_type: Type of test file setup (single_file, multiple_files, etc.)
        test_dir: Path to the test directory
        docker_project_root: Root of the docker project
        validation_info: Dictionary with expected patterns and metadata
        original_omit_entries: Optional list of original omit entries that should be
            present (when merging instead of replacing)
    """
    expected_patterns = validation_info["expected_omit_patterns"]
    test_dir_relative = test_dir.relative_to(docker_project_root)

    # Verify all expected patterns are present (subset check)
    # This works for both merged and non-merged cases
    for pattern in expected_patterns:
        assert pattern in omit_list, (
            f"Expected pattern '{pattern}' not found in omit list"
        )

    # If original omit entries were provided, verify they are also present (merged case)
    if original_omit_entries:
        for original_entry in original_omit_entries:
            assert original_entry in omit_list, (
                f"Original omit entry '{original_entry}' not found in merged omit list"
            )

    # Verify generic patterns are always present
    assert f"{test_dir_relative}/*/test_*.py" in omit_list
    assert f"{test_dir_relative}/**/__init__.py" in omit_list
    assert f"{test_dir_relative}/**/conftest.py" in omit_list

    # Verify other test files are included if they exist
    if validation_info.get("expected_other_test_files"):
        for test_file in validation_info["expected_other_test_files"]:
            assert str(test_dir_relative.joinpath(test_file)) in omit_list

    # Verify target test file is NOT in omit list
    assert str(test_dir_relative.joinpath("test_target.py")) not in omit_list

    # For single_file and multiple_files, if no original entries, verify exact match
    # (to ensure we're not adding unexpected entries)
    if not original_omit_entries:
        if setup_type == "single_file":
            # Should only have the generic patterns (subdirs, __init__, conftest)
            assert set(omit_list) == set(expected_patterns)
        elif setup_type == "multiple_files":
            # Should include the other test files plus generic patterns
            assert set(omit_list) == set(expected_patterns)


def _verify_coverage_settings_preserved(
    config_content: TOMLDocument, original_settings: TOMLDocument
) -> None:
    """Verify that original coverage settings are preserved (except omit).

    Args:
        config_content: Parsed config content from tomlkit
        original_settings: Original coverage settings TOMLDocument
    """
    coverage = config_content["tool"]["coverage"]

    # Verify all original settings from input are preserved (except omit)
    if "run" in original_settings:
        for key, value in original_settings["run"].items():  # type: ignore[attr-defined]
            if key != "omit":  # omit is replaced, not preserved
                assert key in coverage["run"]
                assert coverage["run"][key] == value

    if "report" in original_settings:
        for key, value in original_settings["report"].items():  # type: ignore[attr-defined]
            assert key in coverage["report"]
            assert coverage["report"][key] == value


def _verify_coverage_config_structure(
    coverage: TOMLDocument, setting_type: str, original_settings: TOMLDocument
) -> None:
    """Verify coverage config structure based on setting type.

    Args:
        coverage: The coverage section from parsed config
        setting_type: Type of coverage settings (basic, with_existing_omit, etc.)
        original_settings: Original coverage settings TOMLDocument
    """
    # Common assertion: run section must always exist with omit list
    assert "run" in coverage
    assert "omit" in coverage["run"]
    assert isinstance(coverage["run"]["omit"], list)

    # Verify omit list was merged (not replaced) for with_existing_omit
    if setting_type == "with_existing_omit":
        omit_list = coverage["run"]["omit"]
        # Original omit entries should be preserved
        assert "existing_file.py" in omit_list
        assert "another_file.py" in omit_list
        # New omit patterns should also be present
        assert len(omit_list) > 2  # noqa: PLR2004

    # Verify all original settings are preserved (except omit in run section)
    # Use loops to check each section and key
    for section_name in original_settings:  # type: ignore[attr-defined]
        if section_name == "run":
            # For run section, verify all keys except omit are preserved
            for key, value in original_settings["run"].items():  # type: ignore[attr-defined]
                if key != "omit":  # omit is replaced, not preserved
                    assert key in coverage["run"]
                    assert coverage["run"][key] == value
        else:
            # For other sections (like report), verify all keys are preserved
            assert section_name in coverage
            for key, value in original_settings[section_name].items():  # type: ignore[attr-defined]
                assert key in coverage[section_name]
                assert coverage[section_name][key] == value

    # Verify sections that don't exist in original_settings are not created
    # (except run, which is always created even if not in original_settings)
    original_section_names = set(original_settings.keys())  # type: ignore[attr-defined]
    original_section_names.add("run")  # run is always created
    # Verify only expected sections exist in coverage
    coverage_section_names = set(coverage.keys())
    assert coverage_section_names <= original_section_names, (
        f"Unexpected sections in coverage config: "
        f"{coverage_section_names - original_section_names}"
    )


class TestBuildOmitList:
    """Tests for build_omit_list method."""

    def test_build_omit_list(
        self,
        basic_task_info: BasicTaskInfo,
        docker_project_root: Path,
        test_file_setup: tuple[str, UnitTestInfo, Path, dict[str, Any]],
    ) -> None:
        """Test omit list generation for various test file setups."""
        setup_type, unit_test_info, test_dir, validation_info = test_file_setup

        task = SubprojectUnitTests(
            basic_task_info=basic_task_info,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        )

        omit_list = task.build_omit_list(unit_test_info=unit_test_info)

        # Verify expected patterns based on setup type
        _verify_omit_list_content(
            omit_list=omit_list,
            setup_type=setup_type,
            test_dir=test_dir,
            docker_project_root=docker_project_root,
            validation_info=validation_info,
        )


class TestWriteCoverageConfigFile:
    """Tests for write_coverage_config_file method."""

    def test_write_coverage_config_file(
        self,
        basic_task_info: BasicTaskInfo,
        coverage_settings: tuple[str, TOMLDocument],
        test_file_setup: tuple[str, UnitTestInfo, Path, dict[str, Any]],
    ) -> None:
        """Test writing config file with various settings and test file setups."""
        setting_type, settings = coverage_settings
        setup_type, unit_test_info, test_dir, validation_info = test_file_setup

        task = SubprojectUnitTests(
            basic_task_info=basic_task_info,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        )

        config_path = task.write_coverage_config_file(
            unit_test_info=unit_test_info, coverage_settings=settings
        )

        # Verify file was created
        assert config_path.exists()
        assert config_path.name == "coverage_config_test_target.toml"

        # Parse and verify contents
        config_content = parse(config_path.read_text())
        assert "tool" in config_content
        assert "coverage" in config_content["tool"]
        coverage = config_content["tool"]["coverage"]

        # Verify config structure based on setting type
        _verify_coverage_config_structure(
            coverage=coverage, setting_type=setting_type, original_settings=settings
        )

        # Verify original settings are preserved (except omit)
        _verify_coverage_settings_preserved(
            config_content=config_content, original_settings=settings
        )

    def test_write_coverage_config_preserves_other_settings(
        self,
        basic_task_info: BasicTaskInfo,
        test_file_setup: tuple[str, UnitTestInfo, Path, dict[str, Any]],
    ) -> None:
        """Test that other coverage settings are preserved."""
        setup_type, unit_test_info, test_dir, validation_info = test_file_setup

        task = SubprojectUnitTests(
            basic_task_info=basic_task_info,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        )

        # Create coverage settings with additional fields
        settings = document()
        settings["run"] = table()
        settings["run"]["branch"] = True
        settings["run"]["source"] = ["src"]
        settings["run"]["include"] = ["*.py"]
        settings["report"] = table()
        settings["report"]["precision"] = 2
        settings["report"]["show_missing"] = True

        config_path = task.write_coverage_config_file(
            unit_test_info=unit_test_info, coverage_settings=settings
        )

        # Parse and verify contents
        config_content = parse(config_path.read_text())
        coverage = config_content["tool"]["coverage"]

        # Verify other settings preserved
        assert coverage["run"]["branch"] is True
        assert coverage["run"]["source"] == ["src"]
        assert coverage["run"]["include"] == ["*.py"]
        assert coverage["report"]["precision"] == 2  # noqa: PLR2004
        assert coverage["report"]["show_missing"] is True

        # Verify omit was added/updated
        assert "omit" in coverage["run"]

    def test_write_coverage_config_omit_list_content(
        self,
        basic_task_info: BasicTaskInfo,
        docker_project_root: Path,
        coverage_settings: tuple[str, TOMLDocument],
        test_file_setup: tuple[str, UnitTestInfo, Path, dict[str, Any]],
    ) -> None:
        """Test that the omit list contains expected patterns for various structures."""
        setting_type, settings = coverage_settings
        setup_type, unit_test_info, test_dir, validation_info = test_file_setup

        task = SubprojectUnitTests(
            basic_task_info=basic_task_info,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        )

        config_path = task.write_coverage_config_file(
            unit_test_info=unit_test_info, coverage_settings=settings
        )

        # Parse and verify omit list
        config_content = parse(config_path.read_text())
        omit_list = config_content["tool"]["coverage"]["run"]["omit"]

        # Get original omit entries if they exist (for merge verification)
        original_omit_entries = None
        if setting_type == "with_existing_omit" and "run" in settings:
            original_omit = settings["run"].get("omit")  # type: ignore[attr-defined]
            # existing_omit is always a list when present
            original_omit_entries = list(original_omit) if original_omit else None

        # Verify omit list content based on setup type
        _verify_omit_list_content(
            omit_list=omit_list,
            setup_type=setup_type,
            test_dir=test_dir,
            docker_project_root=docker_project_root,
            validation_info=validation_info,
            original_omit_entries=original_omit_entries,
        )

        # Verify original settings are preserved (except omit)
        _verify_coverage_settings_preserved(
            config_content=config_content, original_settings=settings
        )
