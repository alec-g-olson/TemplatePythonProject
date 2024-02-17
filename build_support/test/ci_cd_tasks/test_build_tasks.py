from pathlib import Path
from unittest.mock import call, patch

from build_support.ci_cd_tasks.build_tasks import (
    BuildAll,
    BuildDocs,
    BuildPypi,
    build_docs_for_subproject,
)
from build_support.ci_cd_tasks.env_setup_tasks import BuildProdEnvironment
from build_support.ci_cd_tasks.test_tasks import TestPypi, TestPythonStyle
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_build_support_docs_build_dir,
    get_build_support_docs_src_dir,
    get_build_support_src_dir,
    get_dist_dir,
    get_pypi_docs_build_dir,
    get_pypi_docs_src_dir,
    get_pypi_src_dir,
    get_sphinx_conf_dir,
    get_temp_dist_dir,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.dag_engine import concatenate_args


def test_build_all_requires():
    assert BuildAll().required_tasks() == [BuildPypi(), BuildDocs()]


def test_run_build_all(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        BuildAll().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 0


def test_build_pypi_requires():
    assert BuildPypi().required_tasks() == [
        TestPypi(),
        TestPythonStyle(),
        BuildProdEnvironment(),
    ]


def test_run_build_pypi(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        clean_dist_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
                "rm",
                "-rf",
                get_dist_dir(project_root=docker_project_root),
            ]
        )
        poetry_build_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
                "poetry",
                "build",
            ]
        )
        mv_dist_to_final_location_args = concatenate_args(
            args=[
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.PROD,
                ),
                "mv",
                get_temp_dist_dir(project_root=docker_project_root),
                get_dist_dir(project_root=docker_project_root),
            ]
        )
        BuildPypi().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 3
        run_process_mock.assert_has_calls(
            calls=[
                call(args=clean_dist_args),
                call(args=poetry_build_args),
                call(args=mv_dist_to_final_location_args),
            ]
        )


def test_build_docs_for_subproject(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    subproject_dir = mock_project_root.joinpath("subprocess_dir")
    subproject_src_dir = subproject_dir.joinpath("src")
    subproject_docs_dir = subproject_dir.joinpath("docs")
    subproject_docs_src_dir = subproject_docs_dir.joinpath("build")
    subproject_docs_build_dir = subproject_docs_dir.joinpath("source")
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        sphinx_api_doc_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-apidoc",
                "-f",
                "--separate",
                "--module-first",
                "--no-toc",
                "-H",
                get_project_name(project_root=docker_project_root),
                "-V",
                get_project_version(project_root=docker_project_root),
                "-o",
                subproject_docs_src_dir,
                subproject_src_dir,
            ]
        )
        sphinx_build_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                subproject_docs_src_dir,
                subproject_docs_build_dir,
                "-c",
                get_sphinx_conf_dir(project_root=docker_project_root),
            ]
        )
        build_docs_for_subproject(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            subproject_src_dir=subproject_src_dir,
            docs_src_dir=subproject_docs_src_dir,
            docs_build_dir=subproject_docs_build_dir,
        )
        assert run_process_mock.call_count == 2
        run_process_mock.assert_has_calls(
            calls=[
                call(args=sphinx_api_doc_args),
                call(args=sphinx_build_args),
            ]
        )


def test_build_docs_requires():
    assert BuildDocs().required_tasks() == [TestPythonStyle()]


def test_run_build_docs(
    mock_project_root: Path,
    mock_docker_pyproject_toml_file: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
):
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        pypi_sphinx_api_doc_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-apidoc",
                "-f",
                "--separate",
                "--module-first",
                "--no-toc",
                "-H",
                get_project_name(project_root=docker_project_root),
                "-V",
                get_project_version(project_root=docker_project_root),
                "-o",
                get_pypi_docs_src_dir(project_root=docker_project_root),
                get_pypi_src_dir(project_root=docker_project_root),
            ]
        )
        pypi_sphinx_build_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                get_pypi_docs_src_dir(project_root=docker_project_root),
                get_pypi_docs_build_dir(project_root=docker_project_root),
                "-c",
                get_sphinx_conf_dir(project_root=docker_project_root),
            ]
        )
        build_support_sphinx_api_doc_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-apidoc",
                "-f",
                "--separate",
                "--module-first",
                "--no-toc",
                "-H",
                get_project_name(project_root=docker_project_root),
                "-V",
                get_project_version(project_root=docker_project_root),
                "-o",
                get_build_support_docs_src_dir(project_root=docker_project_root),
                get_build_support_src_dir(project_root=docker_project_root),
            ]
        )
        build_support_sphinx_build_args = concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=mock_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                get_build_support_docs_src_dir(project_root=docker_project_root),
                get_build_support_docs_build_dir(project_root=docker_project_root),
                "-c",
                get_sphinx_conf_dir(project_root=docker_project_root),
            ]
        )
        BuildDocs().run(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
        assert run_process_mock.call_count == 4
        run_process_mock.assert_has_calls(
            calls=[
                call(args=pypi_sphinx_api_doc_args),
                call(args=pypi_sphinx_build_args),
                call(args=build_support_sphinx_api_doc_args),
                call(args=build_support_sphinx_build_args),
            ]
        )
