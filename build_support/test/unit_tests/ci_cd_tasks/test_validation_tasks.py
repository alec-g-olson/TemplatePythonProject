import shutil
from pathlib import Path
from unittest.mock import call, patch

import pytest
from unit_tests.empty_function_check import is_an_empty_function

from build_support.ci_cd_tasks.env_setup_tasks import GetGitInfo, SetupDevEnvironment
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import (
    AllSubprojectIntegrationTests,
    AllSubprojectSecurityChecks,
    AllSubprojectStaticTypeChecking,
    AllSubprojectUnitTests,
    EnforceProcess,
    SubprojectIntegrationTests,
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
from build_support.ci_cd_vars.project_structure import (
    get_integration_test_scratch_folder,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    get_all_python_subprojects_dict,
    get_python_subproject,
    get_sorted_subproject_contexts,
)
from build_support.file_caching import FileCacheInfo
from build_support.process_runner import concatenate_args


def test_validate_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert ValidateAll(basic_task_info=basic_task_info).required_tasks() == [
        AllSubprojectUnitTests(basic_task_info=basic_task_info),
        ValidatePythonStyle(basic_task_info=basic_task_info),
        AllSubprojectStaticTypeChecking(basic_task_info=basic_task_info),
        AllSubprojectSecurityChecks(basic_task_info=basic_task_info),
        EnforceProcess(basic_task_info=basic_task_info),
        AllSubprojectIntegrationTests(basic_task_info=basic_task_info),
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
                    build_support_subproject.get_pytest_report_args(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                    build_support_subproject.get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.PROCESS_ENFORCEMENT
                    ),
                ],
            )
        )


def test_all_subproject_static_type_checking_requires(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert AllSubprojectStaticTypeChecking(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        ValidateStaticTypeChecking(
            basic_task_info=basic_task_info,
            subproject_context=subproject_context,
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
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    subproject = get_python_subproject(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
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
                    subproject.get_root_dir(),
                ],
            ),
        )


def test_all_subproject_security_checks_requires(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert AllSubprojectSecurityChecks(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        ValidateSecurityChecks(
            basic_task_info=basic_task_info,
            subproject_context=subproject_context,
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_security_checks(
    basic_task_info: BasicTaskInfo,
) -> None:
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
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    subproject = get_python_subproject(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
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
                    subproject.get_bandit_report_path(),
                    "-r",
                    subproject.get_src_dir(),
                ],
            ),
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
                subprojects[SubprojectContext.BUILD_SUPPORT].get_pytest_report_args(
                    test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                ),
                subprojects[SubprojectContext.BUILD_SUPPORT].get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.STYLE_ENFORCEMENT
                ),
            ],
        )
        all_call_args = [
            ruff_check_src_args,
            ruff_check_test_args,
            test_style_enforcement_args,
        ]
        run_process_mock.assert_has_calls(
            calls=[call(args=args) for args in all_call_args],
        )
        assert run_process_mock.call_count == len(all_call_args)


def test_all_subproject_unit_tests_requires(basic_task_info: BasicTaskInfo) -> None:
    assert AllSubprojectUnitTests(basic_task_info=basic_task_info).required_tasks() == [
        SubprojectUnitTests(
            basic_task_info=basic_task_info,
            subproject_context=subproject_context,
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


@pytest.fixture()
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


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_unit_tests_test_all(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    test_subproject_src = mock_docker_subproject.get_python_package_dir()
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

        if test_subproject_src.exists():
            unit_test_root = mock_docker_subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
            )
            src_files = sorted(test_subproject_src.rglob("*"))
            for src_file in src_files:
                if (
                    src_file.is_file()
                    and src_file.name.endswith(".py")
                    and src_file.name != "__init__.py"
                ):
                    relative_path = src_file.relative_to(test_subproject_src)
                    test_folder = unit_test_root.joinpath(relative_path).parent
                    test_file = test_folder.joinpath(f"test_{src_file.name}")
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
                                ],
                            ),
                        )
                    )
                    expected_run_process_calls.append(
                        call(
                            args=concatenate_args(
                                args=[
                                    docker_command,
                                    "coverage",
                                    "report",
                                    "-m",
                                ],
                            ),
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
                            mock_docker_subproject.get_pytest_report_args(
                                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                            ),
                            mock_docker_subproject.get_src_dir(),
                            mock_docker_subproject.get_test_suite_dir(
                                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                            ),
                        ],
                    )
                )
            )
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file", "_mock_entire_subproject")
def test_run_subproject_unit_tests_all_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    src_root = mock_docker_subproject.get_python_package_dir()
    unit_test_root = mock_docker_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    unit_test_cache_file = mock_docker_subproject.get_unit_test_cache_yaml()
    unit_test_cache = FileCacheInfo(
        group_root_dir=mock_docker_subproject.get_root_dir(), cache_info={}
    )
    src_files = sorted(src_root.rglob("*"))
    for src_file in src_files:
        if (
            src_file.is_file()
            and src_file.name.endswith(".py")
            and src_file.name != "__init__.py"
        ):
            relative_path = src_file.relative_to(src_root)
            test_folder = unit_test_root.joinpath(relative_path).parent
            test_file = test_folder.joinpath(f"test_{src_file.name}")
            unit_test_cache.file_has_been_changed(file_path=src_file)
            unit_test_cache.file_has_been_changed(file_path=test_file)
    unit_test_cache_file.write_text(unit_test_cache.to_yaml())
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
def test_run_subproject_unit_tests_some_cached(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    mock_docker_subproject: PythonSubproject,
) -> None:
    src_root = mock_docker_subproject.get_python_package_dir()
    unit_test_root = mock_docker_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    unit_test_cache_file = mock_docker_subproject.get_unit_test_cache_yaml()
    unit_test_cache = FileCacheInfo(
        group_root_dir=mock_docker_subproject.get_root_dir(), cache_info={}
    )
    src_files = sorted(src_root.rglob("*"))
    src_files_to_skip_tests_for = []
    file_index = 0
    cache_both_src_and_test = 0
    cache_both_src = 1
    cache_both_test = 2
    for src_file in src_files:
        if (
            src_file.is_file()
            and src_file.name.endswith(".py")
            and src_file.name != "__init__.py"
        ):
            relative_path = src_file.relative_to(src_root)
            test_folder = unit_test_root.joinpath(relative_path).parent
            test_file = test_folder.joinpath(f"test_{src_file.name}")
            mod_twenty = file_index % 10
            if mod_twenty == cache_both_src_and_test:
                # both src and test are cached skip testing pair of files
                unit_test_cache.file_has_been_changed(file_path=src_file)
                unit_test_cache.file_has_been_changed(file_path=test_file)
                src_files_to_skip_tests_for.append(src_file)
            elif mod_twenty == cache_both_src:
                # cache src but not test, testing needs to happen
                unit_test_cache.file_has_been_changed(file_path=src_file)
            elif mod_twenty == cache_both_test:
                # cache test but not src, testing needs to happen
                unit_test_cache.file_has_been_changed(file_path=test_file)
            file_index += 1
    unit_test_cache_file.write_text(unit_test_cache.to_yaml())
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
        docker_command = get_docker_command_for_image(
            non_docker_project_root=basic_task_info.non_docker_project_root,
            docker_project_root=basic_task_info.docker_project_root,
            target_image=DockerTarget.DEV,
        )
        expected_run_process_calls = []
        skipped_tests = 0
        if src_root.exists():
            assert len(src_files_to_skip_tests_for) > 0
            unit_test_root = mock_docker_subproject.get_test_suite_dir(
                test_suite=PythonSubproject.TestSuite.UNIT_TESTS
            )
            src_files = sorted(src_root.rglob("*"))
            for src_file in src_files:
                if (
                    src_file.is_file()
                    and src_file.name.endswith(".py")
                    and src_file.name != "__init__.py"
                ):
                    if src_file in src_files_to_skip_tests_for:
                        skipped_tests += 1
                        continue
                    relative_path = src_file.relative_to(src_root)
                    test_folder = unit_test_root.joinpath(relative_path).parent
                    test_file = test_folder.joinpath(f"test_{src_file.name}")
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
                                ],
                            ),
                        )
                    )
                    expected_run_process_calls.append(
                        call(
                            args=concatenate_args(
                                args=[
                                    docker_command,
                                    "coverage",
                                    "report",
                                    "-m",
                                ],
                            ),
                        )
                    )
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
                                mock_docker_subproject.get_pytest_report_args(
                                    test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                                ),
                                mock_docker_subproject.get_src_dir(),
                                mock_docker_subproject.get_test_suite_dir(
                                    test_suite=PythonSubproject.TestSuite.UNIT_TESTS
                                ),
                            ],
                        )
                    )
                )
        assert skipped_tests == len(src_files_to_skip_tests_for)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_all_subproject_integration_tests_requires(
    basic_task_info: BasicTaskInfo,
) -> None:
    assert AllSubprojectIntegrationTests(
        basic_task_info=basic_task_info
    ).required_tasks() == [
        SubprojectIntegrationTests(
            basic_task_info=basic_task_info,
            subproject_context=subproject_context,
        )
        for subproject_context in get_sorted_subproject_contexts()
    ]


def test_run_all_subproject_integration_tests(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(
        func=AllSubprojectIntegrationTests(basic_task_info=basic_task_info).run
    )


def test_subproject_integration_tests_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    if subproject_context == SubprojectContext.BUILD_SUPPORT:
        assert SubprojectIntegrationTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [
            SubprojectUnitTests(
                basic_task_info=basic_task_info, subproject_context=subproject_context
            ),
            ValidatePythonStyle(basic_task_info=basic_task_info),
            EnforceProcess(basic_task_info=basic_task_info),
        ]
    else:
        assert SubprojectIntegrationTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).required_tasks() == [
            SubprojectUnitTests(
                basic_task_info=basic_task_info, subproject_context=subproject_context
            )
        ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_subproject_integration_tests(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    subproject = get_python_subproject(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectIntegrationTests(
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
                    "pytest",
                    "--basetemp",
                    get_integration_test_scratch_folder(
                        project_root=basic_task_info.docker_project_root
                    ),
                    subproject.get_pytest_report_args(
                        test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
                    ),
                    subproject.get_test_suite_dir(
                        test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
                    ),
                ],
            ),
        )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_subproject_integration_tests_in_ci_cd_int_test_mode(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    basic_task_info.ci_cd_integration_test_mode = True
    subproject = get_python_subproject(
        subproject_context=subproject_context,
        project_root=basic_task_info.docker_project_root,
    )
    with patch(
        "build_support.ci_cd_tasks.validation_tasks.run_process"
    ) as run_process_mock:
        SubprojectIntegrationTests(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        expected_called_with = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "pytest",
                "--basetemp",
                get_integration_test_scratch_folder(
                    project_root=basic_task_info.docker_project_root
                ),
                subproject.get_pytest_report_args(
                    test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
                ),
                subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
                ),
            ],
        )
        if subproject_context == SubprojectContext.BUILD_SUPPORT:
            run_process_mock.assert_not_called()
        else:
            run_process_mock.assert_called_once_with(args=expected_called_with)
