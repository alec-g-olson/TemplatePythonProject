from unittest.mock import call, patch

import pytest
from test_utils.empty_function_check import (  # type: ignore[import-untyped]
    is_an_empty_function,
)

from build_support.ci_cd_tasks.build_tasks import BuildAll, BuildDocs, BuildPypi
from build_support.ci_cd_tasks.env_setup_tasks import SetupProdEnvironment
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import (
    SubprojectUnitTests,
    ValidatePythonStyle,
)
from build_support.ci_cd_vars.build_paths import (
    get_build_docs_build_dir,
    get_build_docs_source_dir,
    get_dist_dir,
)
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.project_structure import get_docs_dir, get_sphinx_conf_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args


def test_build_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert BuildAll(basic_task_info=basic_task_info).required_tasks() == [
        BuildPypi(basic_task_info=basic_task_info),
        BuildDocs(basic_task_info=basic_task_info),
    ]


def test_run_build_all(basic_task_info: BasicTaskInfo) -> None:
    assert is_an_empty_function(func=BuildAll(basic_task_info=basic_task_info).run)


def test_build_pypi_requires(basic_task_info: BasicTaskInfo) -> None:
    assert BuildPypi(basic_task_info=basic_task_info).required_tasks() == [
        SubprojectUnitTests(
            basic_task_info=basic_task_info, subproject_context=SubprojectContext.PYPI
        ),
        ValidatePythonStyle(basic_task_info=basic_task_info),
        SetupProdEnvironment(basic_task_info=basic_task_info),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_pypi(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        clean_dist_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
                "rm",
                "-rf",
                get_dist_dir(project_root=basic_task_info.docker_project_root),
            ]
        )
        poetry_build_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
                "poetry",
                "build",
                "--output",
                get_dist_dir(project_root=basic_task_info.docker_project_root),
            ]
        )
        BuildPypi(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=clean_dist_args),
            call(args=poetry_build_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_build_docs_requires(basic_task_info: BasicTaskInfo) -> None:
    assert BuildDocs(basic_task_info=basic_task_info).required_tasks() == [
        ValidatePythonStyle(basic_task_info=basic_task_info)
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_docs(basic_task_info: BasicTaskInfo) -> None:
    with (
        patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock,
        patch("build_support.ci_cd_tasks.build_tasks.copytree") as copytree_mock,
        patch(
            "build_support.ci_cd_tasks.build_tasks.get_all_python_subprojects_with_src"
        ) as mock_get_subprojects_with_src,
    ):
        mock_subprojects_with_docs = [
            get_python_subproject(
                subproject_context=SubprojectContext.BUILD_SUPPORT,
                project_root=basic_task_info.docker_project_root,
            ),
            get_python_subproject(
                subproject_context=SubprojectContext.PYPI,
                project_root=basic_task_info.docker_project_root,
            ),
        ]
        mock_get_subprojects_with_src.return_value = mock_subprojects_with_docs
        sphinx_api_doc_args_list = [
            concatenate_args(
                [
                    get_docker_command_for_image(
                        non_docker_project_root=basic_task_info.non_docker_project_root,
                        docker_project_root=basic_task_info.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "sphinx-apidoc",
                    "-f",
                    "--separate",
                    "--module-first",
                    "--no-toc",
                    "-H",
                    get_project_name(project_root=basic_task_info.docker_project_root),
                    "-V",
                    get_project_version(
                        project_root=basic_task_info.docker_project_root
                    ),
                    "-o",
                    get_build_docs_source_dir(
                        project_root=basic_task_info.docker_project_root
                    ),
                    current_subproject.get_src_dir(),
                ]
            )
            for current_subproject in mock_subprojects_with_docs
        ]
        sphinx_build_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                get_build_docs_source_dir(
                    project_root=basic_task_info.docker_project_root
                ),
                get_build_docs_build_dir(
                    project_root=basic_task_info.docker_project_root
                ),
                "-c",
                get_sphinx_conf_dir(project_root=basic_task_info.docker_project_root),
            ]
        )
        BuildDocs(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=sphinx_api_doc_args)
            for sphinx_api_doc_args in sphinx_api_doc_args_list
        ] + [call(args=sphinx_build_args)]
        copytree_mock.assert_called_once_with(
            src=get_docs_dir(project_root=basic_task_info.docker_project_root),
            dst=get_build_docs_source_dir(
                project_root=basic_task_info.docker_project_root
            ),
            dirs_exist_ok=True,
        )
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)
