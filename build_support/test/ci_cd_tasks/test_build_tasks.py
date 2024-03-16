from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.build_tasks import (
    BuildAll,
    BuildAllDocs,
    BuildDocs,
    BuildPypi,
)
from build_support.ci_cd_tasks.env_setup_tasks import SetupProdEnvironment
from build_support.ci_cd_tasks.task_node import BasicTaskInfo
from build_support.ci_cd_tasks.validation_tasks import ValidatePypi, ValidatePythonStyle
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_dist_dir,
    get_sphinx_conf_dir,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_all_python_subprojects_dict,
)
from build_support.process_runner import concatenate_args


def test_build_all_requires(basic_task_info: BasicTaskInfo) -> None:
    assert BuildAll(basic_task_info=basic_task_info).required_tasks() == [
        BuildPypi(basic_task_info=basic_task_info),
        BuildAllDocs(basic_task_info=basic_task_info),
    ]


def test_run_build_all(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        BuildAll(basic_task_info=basic_task_info).run()
        assert run_process_mock.call_count == 0


def test_build_pypi_requires(basic_task_info: BasicTaskInfo) -> None:
    assert BuildPypi(basic_task_info=basic_task_info).required_tasks() == [
        ValidatePypi(basic_task_info=basic_task_info),
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
            ],
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
            ],
        )
        BuildPypi(basic_task_info=basic_task_info).run()
        expected_run_process_calls = [
            call(args=clean_dist_args),
            call(args=poetry_build_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_build_all_docs_requires(basic_task_info: BasicTaskInfo) -> None:
    subprojects = get_all_python_subprojects_dict(
        project_root=basic_task_info.docker_project_root
    )
    # Only builds documentation if documentation dir exists.
    pulumi_docs_dir = subprojects[SubprojectContext.PULUMI].get_docs_dir()
    pulumi_docs_dir.mkdir(parents=True, exist_ok=True)
    build_support_docs_dir = subprojects[SubprojectContext.BUILD_SUPPORT].get_docs_dir()
    build_support_docs_dir.mkdir(parents=True, exist_ok=True)

    assert BuildAllDocs(basic_task_info=basic_task_info).required_tasks() == [
        BuildDocs(
            basic_task_info=basic_task_info,
            subproject_context=SubprojectContext.BUILD_SUPPORT,
        ),
        BuildDocs(
            basic_task_info=basic_task_info, subproject_context=SubprojectContext.PULUMI
        ),
    ]


def test_run_build_docs_all(basic_task_info: BasicTaskInfo) -> None:
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        BuildAllDocs(basic_task_info=basic_task_info).run()
        assert run_process_mock.call_count == 0


def test_build_docs_requires(
    basic_task_info: BasicTaskInfo, subproject_context: SubprojectContext
) -> None:
    assert BuildDocs(
        basic_task_info=basic_task_info, subproject_context=subproject_context
    ).required_tasks() == [ValidatePythonStyle(basic_task_info=basic_task_info)]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_docs(
    basic_task_info: BasicTaskInfo,
    subproject_context: SubprojectContext,
    subproject: PythonSubproject,
) -> None:
    with (
        patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock,
        patch("build_support.ci_cd_tasks.build_tasks.copytree") as copytree_mock,
    ):
        sphinx_api_doc_args = concatenate_args(
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
                get_project_version(project_root=basic_task_info.docker_project_root),
                "-o",
                subproject.get_build_docs_source_dir(),
                subproject.get_src_dir(),
            ],
        )
        sphinx_build_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=basic_task_info.non_docker_project_root,
                    docker_project_root=basic_task_info.docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                subproject.get_build_docs_source_dir(),
                subproject.get_build_docs_build_dir(),
                "-c",
                get_sphinx_conf_dir(project_root=basic_task_info.docker_project_root),
            ],
        )
        BuildDocs(
            basic_task_info=basic_task_info, subproject_context=subproject_context
        ).run()
        expected_run_process_calls = [
            call(args=sphinx_api_doc_args),
            call(args=sphinx_build_args),
        ]
        copytree_mock.assert_called_once_with(
            src=subproject.get_docs_dir(),
            dst=subproject.get_build_docs_source_dir(),
        )
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)
