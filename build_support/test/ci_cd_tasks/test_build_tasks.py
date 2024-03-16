from pathlib import Path
from unittest.mock import call, patch

import pytest

from build_support.ci_cd_tasks.build_tasks import (
    BuildAll,
    BuildDocs,
    BuildPypi,
    build_docs_for_subproject,
)
from build_support.ci_cd_tasks.env_setup_tasks import SetupProdEnvironment
from build_support.ci_cd_tasks.validation_tasks import ValidatePypi, ValidatePythonStyle
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
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.process_runner import concatenate_args


def test_build_all_requires(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
    assert BuildAll(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    ).required_tasks() == [
        BuildPypi(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
        BuildDocs(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
    ]


def test_run_build_all(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
    with patch("build_support.ci_cd_tasks.build_tasks.run_process") as run_process_mock:
        BuildAll(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ).run()
        assert run_process_mock.call_count == 0


def test_build_pypi_requires(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
    assert BuildPypi(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    ).required_tasks() == [
        ValidatePypi(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
        ValidatePythonStyle(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
        SetupProdEnvironment(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ),
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_pypi(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
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
            ],
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
                "--output",
                get_dist_dir(project_root=docker_project_root),
            ],
        )
        BuildPypi(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ).run()
        expected_run_process_calls = [
            call(args=clean_dist_args),
            call(args=poetry_build_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_build_docs_for_subproject(
    mock_project_root: Path,
    docker_project_root: Path,
) -> None:
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
            ],
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
            ],
        )
        build_docs_for_subproject(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            subproject_src_dir=subproject_src_dir,
            docs_src_dir=subproject_docs_src_dir,
            docs_build_dir=subproject_docs_build_dir,
        )
        expected_run_process_calls = [
            call(args=sphinx_api_doc_args),
            call(args=sphinx_build_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)


def test_build_docs_requires(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
    assert BuildDocs(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        local_user_uid=local_uid,
        local_user_gid=local_gid,
    ).required_tasks() == [
        ValidatePythonStyle(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        )
    ]


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_run_build_docs(
    mock_project_root: Path,
    docker_project_root: Path,
    local_uid: int,
    local_gid: int,
) -> None:
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
            ],
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
            ],
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
            ],
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
            ],
        )
        BuildDocs(
            non_docker_project_root=mock_project_root,
            docker_project_root=docker_project_root,
            local_user_uid=local_uid,
            local_user_gid=local_gid,
        ).run()
        expected_run_process_calls = [
            call(args=pypi_sphinx_api_doc_args),
            call(args=pypi_sphinx_build_args),
            call(args=build_support_sphinx_api_doc_args),
            call(args=build_support_sphinx_build_args),
        ]
        assert run_process_mock.call_count == len(expected_run_process_calls)
        run_process_mock.assert_has_calls(calls=expected_run_process_calls)
