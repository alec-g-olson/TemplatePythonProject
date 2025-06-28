import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from time import sleep
from typing import Any
from unittest.mock import call, patch

import pytest
from junitparser import JUnitXml, TestCase, TestSuite
from unit_tests.empty_function_check import is_an_empty_function

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import (
    AllSubprojectFeatureTests,
    AllSubprojectSecurityChecks,
    AllSubprojectStaticTypeChecking,
    AllSubprojectUnitTests,
    EnforceProcess,
    SubprojectFeatureTests,
    SubprojectUnitTests,
    ValidateAll,
    ValidatePythonStyle,
    ValidateSecurityChecks,
    ValidateStaticTypeChecking,
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
from build_support.ci_cd_vars.project_structure import get_feature_test_scratch_folder
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    get_all_python_subprojects_dict,
    get_python_subproject,
    get_sorted_subproject_contexts,
)
from build_support.file_caching import FileCacheEngine
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
    if subproject_context == SubprojectContext.BUILD_SUPPORT:
        assert SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [
            SetupDevEnvironment(basic_task_info=basic_task_info),
            GetGitInfo(basic_task_info=basic_task_info),
        ]
    else:
        assert SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [SetupDevEnvironment(basic_task_info=basic_task_info)]


@pytest.fixture
def _mock_entire_subproject(
    real_project_root_dir: Path,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    real_subproject = get_python_subproject(
        project_root=real_project_root_dir, subproject_context=subproject_context
    ).get_root_dir()
    test_subproject = mock_docker_subproject.get_root_dir()
    shutil.copytree(src=real_subproject, dst=test_subproject)


def _recursive_get_conftest_files(current_test_folder: Path) -> Iterator[Path]:
    """A method to recursively get the all test folders.

    Args:
        current_test_folder (Path): Path to the test folder being traversed.

    Yields:
        Iterator[UnitTestInfo]: Generator of unit test info for test caching.
    """
    paths_in_dir = sorted(current_test_folder.glob("*"))
    maybe_conftest = current_test_folder.joinpath(FileCacheEngine.CONFTEST_NAME)
    if maybe_conftest.exists():
        yield maybe_conftest
    dirs = [path for path in paths_in_dir if path.is_dir()]
    for directory in dirs:
        yield from _recursive_get_conftest_files(current_test_folder=directory)


def get_all_conftest_files(
    subproject: PythonSubproject, cache_info_suite: FileCacheEngine.CacheInfoSuite
) -> list[Path]:
    """Gets a list of all the conftest files for the relevant suite of cache info.

    Args:
        subproject (PythonSubproject): Th
        cache_info_suite (CacheInfoSuite): The suite of relevant cache info.

    Returns:
        list[Path]: All the relevant conftests for the suite of relevant cache info.
    """
    files = [subproject.get_test_dir().joinpath(FileCacheEngine.CONFTEST_NAME)]
    files[0].parent.mkdir(parents=True, exist_ok=True)
    files[0].touch()
    if cache_info_suite == FileCacheEngine.CacheInfoSuite.UNIT_TEST:
        files.extend(
            _recursive_get_conftest_files(
                subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                )
            )
        )
    elif cache_info_suite == FileCacheEngine.CacheInfoSuite.FEATURE_TEST:
        files.extend(
            _recursive_get_conftest_files(
                subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
                )
            )
        )
    else:  # pragma: no cov - will only hit if enum not covered
        msg = f"{cache_info_suite.__name__} is not a supported type."
        raise ValueError(msg)
    return files


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_unit_tests_test_all(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        cache_engine = FileCacheEngine(
            subproject_context=subproject_context,
            project_root=basic_task_info.docker_project_root,
        )
        top_level_conftest = cache_engine.subproject.get_test_dir().joinpath(
            FileCacheEngine.CONFTEST_NAME
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
        for unit_test_info in cache_engine.get_unit_test_info():
            for src_file, test_file in unit_test_info.src_test_file_pairs:
                expected_run_process_calls.append(
                    call(
                        args=concatenate_args(
                            args=[
                                docker_command,
                                "coverage",
                                "run",
                                "--include",
                                src_file,
                                "-m",
                                "pytest",
                                test_file,
                            ]
                        )
                    )
                )
                expected_run_process_calls.append(
                    call(
                        args=concatenate_args(
                            args=[docker_command, "coverage", "report", "-m"]
                        )
                    )
                )
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
        run_process_mock.assert_has_calls(
            calls=expected_run_process_calls, any_order=True
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_unit_tests_all_cached(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    cache_engine = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    cache_info_suite = FileCacheEngine.CacheInfoSuite.UNIT_TEST
    for conftest_file in get_all_conftest_files(
        subproject=cache_engine.subproject, cache_info_suite=cache_info_suite
    ):
        cache_engine.file_has_been_changed(
            file_path=conftest_file, cache_info_suite=cache_info_suite
        )
    for unit_test_info in cache_engine.get_unit_test_info():
        for src_file, test_file in unit_test_info.src_test_file_pairs:
            cache_engine.file_has_been_changed(
                file_path=src_file, cache_info_suite=cache_info_suite
            )
            cache_engine.file_has_been_changed(
                file_path=test_file, cache_info_suite=cache_info_suite
            )
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


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_unit_tests_all_cached_but_top_test_conftest_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    cache_engine = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    cache_info_suite = FileCacheEngine.CacheInfoSuite.UNIT_TEST
    for conftest_file in get_all_conftest_files(
        subproject=mock_docker_subproject, cache_info_suite=cache_info_suite
    ):
        cache_engine.file_has_been_changed(
            file_path=conftest_file, cache_info_suite=cache_info_suite
        )
    for unit_test_info in cache_engine.get_unit_test_info():
        for src_file, test_file in unit_test_info.src_test_file_pairs:
            cache_engine.file_has_been_changed(
                file_path=src_file, cache_info_suite=cache_info_suite
            )
            cache_engine.file_has_been_changed(
                file_path=test_file, cache_info_suite=cache_info_suite
            )
    cache_engine.write_text()
    sleep(10 / 1000)  # sleep just long enough for a new timestamp when writing file
    mock_docker_subproject.get_test_dir().joinpath(
        FileCacheEngine.CONFTEST_NAME
    ).write_text("Updated Top Level Conftest")
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
        for unit_test_info in cache_engine.get_unit_test_info():
            for src_file, test_file in unit_test_info.src_test_file_pairs:
                expected_run_process_calls.append(
                    call(
                        args=concatenate_args(
                            args=[
                                docker_command,
                                "coverage",
                                "run",
                                "--include",
                                src_file,
                                "-m",
                                "pytest",
                                test_file,
                            ]
                        )
                    )
                )
                expected_run_process_calls.append(
                    call(
                        args=concatenate_args(
                            args=[docker_command, "coverage", "report", "-m"]
                        )
                    )
                )
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
        run_process_mock.assert_has_calls(
            calls=expected_run_process_calls, any_order=True
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
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
    cache_both_src = 1
    cache_both_test = 2
    cache_engine = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    file_index = 0
    cache_info_suite = FileCacheEngine.CacheInfoSuite.UNIT_TEST
    for conftest_file in get_all_conftest_files(
        subproject=cache_engine.subproject, cache_info_suite=cache_info_suite
    ):
        # testing a scenario where no conftest files have been updated
        cache_engine.file_has_been_changed(
            file_path=conftest_file, cache_info_suite=cache_info_suite
        )
    for unit_test_info in cache_engine.get_unit_test_info():
        for src_file, test_file in unit_test_info.src_test_file_pairs:
            pair_run_process_calls = [
                call(
                    args=concatenate_args(
                        args=[
                            docker_command,
                            "coverage",
                            "run",
                            "--include",
                            src_file,
                            "-m",
                            "pytest",
                            test_file,
                        ]
                    )
                ),
                call(
                    args=concatenate_args(
                        args=[docker_command, "coverage", "report", "-m"]
                    )
                ),
            ]
            mod_ten = file_index % 10
            if mod_ten == cache_both_src_and_test:
                # both src and test are cached skip testing pair of files
                file_cache.file_has_been_changed(
                    file_path=src_file, cache_info_suite=cache_info_suite
                )
                file_cache.file_has_been_changed(
                    file_path=test_file, cache_info_suite=cache_info_suite
                )
            elif mod_ten == cache_both_src:
                # cache src but not test, testing needs to happen
                file_cache.file_has_been_changed(
                    file_path=src_file, cache_info_suite=cache_info_suite
                )
                expected_run_process_calls.extend(pair_run_process_calls)
            elif mod_ten == cache_both_test:
                # cache test but not src, testing needs to happen
                file_cache.file_has_been_changed(
                    file_path=test_file, cache_info_suite=cache_info_suite
                )
                expected_run_process_calls.extend(pair_run_process_calls)
            else:
                expected_run_process_calls.extend(pair_run_process_calls)
            file_index += 1
    file_cache.write_text()
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
        run_process_mock.assert_has_calls(
            calls=expected_run_process_calls, any_order=True
        )


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
    if subproject_context == SubprojectContext.BUILD_SUPPORT:
        assert SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [
            SubprojectUnitTests(
                basic_task_info=basic_task_info, subproject_context=subproject_context
            ),
            ValidatePythonStyle(basic_task_info=basic_task_info),
            EnforceProcess(basic_task_info=basic_task_info),
        ]
    else:
        assert SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [
            SubprojectUnitTests(
                basic_task_info=basic_task_info, subproject_context=subproject_context
            )
        ]


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


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
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
        file_cache = FileCacheEngine(
            subproject_context=subproject_context, project_root=docker_project_root
        )
        feature_test_info = file_cache.get_feature_test_info()
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
            for test_file_to_run in feature_test_info.test_files
        ]
        if len(expected_calls) > 0:
            run_process_mock.assert_has_calls(calls=expected_calls)
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
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
        file_cache = FileCacheEngine(
            subproject_context=subproject_context, project_root=docker_project_root
        )
        feature_test_info = file_cache.get_feature_test_info()
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
            for test_file_to_run in feature_test_info.test_files
        ]
        if subproject_context == SubprojectContext.BUILD_SUPPORT:
            run_process_mock.assert_not_called()
        else:
            run_process_mock.assert_has_calls(calls=expected_calls)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_feature_tests_all_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    feature_test_info = file_cache.get_feature_test_info()
    for file in (
        *feature_test_info.src_files,
        *feature_test_info.test_files,
        *get_all_conftest_files(
            subproject=mock_docker_subproject,
            cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
        ),
    ):
        file_cache.file_has_been_changed(
            file_path=file, cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST
        )
    file_cache.write_text()
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectFeatureTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        run_process_mock.assert_not_called()


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_feature_tests_all_cached_but_top_test_conftest_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    feature_test_info = file_cache.get_feature_test_info()
    for file in (
        *feature_test_info.src_files,
        *feature_test_info.test_files,
        *get_all_conftest_files(
            subproject=mock_docker_subproject,
            cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
        ),
    ):
        file_cache.file_has_been_changed(
            file_path=file, cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST
        )
    file_cache.write_text()
    sleep(10 / 1000)  # sleep just long enough for a new timestamp when writing file
    mock_docker_subproject.get_test_dir().joinpath(
        FileCacheEngine.CONFTEST_NAME
    ).write_text("Updated Top Level Conftest")

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
            for test_file_to_run in feature_test_info.test_files
        ]
        if len(expected_calls) > 0:
            run_process_mock.assert_has_calls(calls=expected_calls)
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_feature_tests_some_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    feature_test_info = file_cache.get_feature_test_info()
    if len(feature_test_info.test_files) <= 1:  # pragma: no cov - might not be true
        return

    for file in (
        *feature_test_info.src_files,
        feature_test_info.test_files[0],
        *get_all_conftest_files(
            subproject=mock_docker_subproject,
            cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
        ),
    ):
        file_cache.file_has_been_changed(
            file_path=file, cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST
        )
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
            for test_file_to_run in feature_test_info.test_files[1:]
        ]
        run_process_mock.assert_has_calls(calls=expected_calls)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_feature_tests_one_src_updated(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    feature_test_info = file_cache.get_feature_test_info()
    if len(feature_test_info.src_files) <= 1:  # pragma: no cov - might not be true
        return

    file_cache = FileCacheEngine(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    feature_test_info = file_cache.get_feature_test_info()
    for file in (
        *feature_test_info.src_files,
        *feature_test_info.test_files,
        *get_all_conftest_files(
            subproject=mock_docker_subproject,
            cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
        ),
    ):
        file_cache.file_has_been_changed(
            file_path=file, cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST
        )
    file_cache.write_text()
    sleep(10 / 1000)  # sleep just long enough for a new timestamp when writing file
    src_file = feature_test_info.src_files[0]
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
                        test_file_to_run,
                    ]
                )
            )
            for test_file_to_run in feature_test_info.test_files
        ]
        if len(expected_calls) > 0:
            run_process_mock.assert_has_calls(calls=expected_calls)
        else:  # pragma: no cov - might only have cases that require calls
            run_process_mock.assert_not_called()
