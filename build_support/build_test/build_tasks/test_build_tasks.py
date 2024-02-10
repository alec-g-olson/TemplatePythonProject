from pathlib import Path
from unittest.mock import call, patch

from build_tasks.build_tasks import BuildPypi
from build_tasks.env_setup_tasks import BuildProdEnvironment
from build_tasks.test_tasks import TestPypi, TestPythonStyle
from build_vars.docker_vars import DockerTarget, get_docker_command_for_image
from build_vars.file_and_dir_path_vars import get_dist_dir, get_temp_dist_dir
from dag_engine import concatenate_args


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
    with patch("build_tasks.build_tasks.run_process") as run_process_mock:
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
