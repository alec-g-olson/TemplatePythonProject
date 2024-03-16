from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_base_docker_command_for_image,
    get_docker_build_command,
    get_docker_command_for_image,
    get_docker_image_name,
    get_interactive_docker_command_for_image,
    get_mypy_path_env,
    get_python_path_env,
    get_python_path_for_target_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_python_folders,
)
from build_support.ci_cd_vars.project_structure import get_dockerfile
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args

docker_targets = list(DockerTarget)
test_project_names = ["test_project_one", "some_other_project"]


@pytest.fixture(params=docker_targets)
def docker_target(request: SubRequest) -> DockerTarget:
    return request.param


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_image_name(
    mock_project_root: Path,
    project_name: str,
    docker_target: DockerTarget,
) -> None:
    assert (
        get_docker_image_name(
            project_root=mock_project_root,
            target_image=docker_target,
        )
        == f"{project_name}:{docker_target.value}"
    )


def test_get_python_path_for_target_image(
    docker_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    observed_python_path = get_python_path_for_target_image(
        docker_project_root=docker_project_root,
        target_image=docker_target,
    )

    if docker_target == DockerTarget.BUILD:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.BUILD_SUPPORT,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ],
            ),
        )
    elif docker_target == DockerTarget.DEV:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[get_all_python_folders(project_root=docker_project_root)],
            ),
        )
    elif docker_target == DockerTarget.PROD:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.PYPI,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            ),
        )
    else:  # assume pulumi if not add the new case
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.PULUMI,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            ),
        )


def test_get_python_path_env(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_python_path_env(
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == "PYTHONPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root,
        target_image=docker_target,
    )


def test_get_mypy_path_env(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_mypy_path_env(
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == "MYPYPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root,
        target_image=docker_target,
    )


def test_get_base_docker_command_for_image(
    mock_project_root: Path,
    docker_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    assert get_base_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        args=[
            "docker",
            "run",
            "--rm",
            f"--workdir={docker_project_root.absolute()}",
            "-e",
            get_python_path_env(
                docker_project_root=docker_project_root,
                target_image=docker_target,
            ),
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-v",
            ":".join(
                concatenate_args(
                    args=[
                        mock_project_root.absolute(),
                        docker_project_root.absolute(),
                    ],
                ),
            ),
        ],
    )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_get_docker_command_for_image(
    mock_project_root: Path,
    docker_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    assert get_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        [
            get_base_docker_command_for_image(
                non_docker_project_root=mock_project_root,
                docker_project_root=docker_project_root,
                target_image=docker_target,
            ),
            get_docker_image_name(
                project_root=docker_project_root,
                target_image=docker_target,
            ),
        ],
    )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_get_interactive_docker_command_for_image(
    mock_project_root: Path,
    docker_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    assert get_interactive_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        [
            get_base_docker_command_for_image(
                non_docker_project_root=mock_project_root,
                docker_project_root=docker_project_root,
                target_image=docker_target,
            ),
            "-it",
            get_docker_image_name(
                project_root=docker_project_root,
                target_image=docker_target,
            ),
        ],
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_build_command_no_extras(
    mock_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    standard = get_docker_build_command(
        project_root=mock_project_root,
        target_image=docker_target,
    )
    no_extra_explicit = get_docker_build_command(
        project_root=mock_project_root,
        target_image=docker_target,
        extra_args=None,
    )
    empty_extra_args = get_docker_build_command(
        project_root=mock_project_root,
        target_image=docker_target,
        extra_args={},
    )
    assert standard == no_extra_explicit
    assert standard == empty_extra_args
    assert standard == concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=mock_project_root),
            "--target",
            docker_target.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            [],
            "-t",
            get_docker_image_name(
                project_root=mock_project_root,
                target_image=docker_target,
            ),
            mock_project_root.absolute(),
        ],
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_build_command_with_extras(
    mock_project_root: Path,
    docker_target: DockerTarget,
) -> None:
    assert get_docker_build_command(
        project_root=mock_project_root,
        target_image=docker_target,
        extra_args={"--some-key": 8, "--no-val-with-key": None, "--other": "whee"},
    ) == concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=mock_project_root),
            "--target",
            docker_target.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            ["--some-key", "8", "--no-val-with-key", "--other", "whee"],
            "-t",
            get_docker_image_name(
                project_root=mock_project_root,
                target_image=docker_target,
            ),
            mock_project_root.absolute(),
        ],
    )
