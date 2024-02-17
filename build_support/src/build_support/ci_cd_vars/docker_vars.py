"""A place to hold tasks and variable used for launching docker."""

from enum import Enum
from pathlib import Path
from typing import Any

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_python_folders,
    get_build_support_src_dir,
    get_dockerfile,
    get_pulumi_dir,
    get_pypi_src_dir,
)
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.dag_engine import concatenate_args


class DockerTarget(Enum):
    """An Enum to track the possible docker targets and images."""

    BUILD = "build"
    DEV = "dev"
    PROD = "prod"
    PULUMI = "pulumi"


def get_docker_image_name(project_root: Path, target_image: DockerTarget) -> str:
    """Gets the docker image name for a target."""
    return ":".join([get_project_name(project_root=project_root), target_image.value])


def get_python_path_for_target_image(
    docker_project_root: Path, target_image: DockerTarget
) -> str:
    """Gets the python path to use with this project."""
    match target_image:
        case DockerTarget.BUILD:
            python_folders: Path | list[str] = get_build_support_src_dir(
                project_root=docker_project_root
            )
        case DockerTarget.DEV:
            python_folders = get_all_python_folders(project_root=docker_project_root)
        case DockerTarget.PROD:
            python_folders = get_pypi_src_dir(project_root=docker_project_root)
        case DockerTarget.PULUMI:
            python_folders = get_pulumi_dir(project_root=docker_project_root)
        case _:  # pragma: no cover - can't hit if all enums are implemented
            raise ValueError(f"{repr(target_image)} is not a valid enum of DockerType.")
    return ":".join(concatenate_args(args=[python_folders]))


def get_python_path_env(docker_project_root: Path, target_image: DockerTarget) -> str:
    """Gets the python path ENV to use with this project."""
    return "PYTHONPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root, target_image=target_image
    )


def get_mypy_path_env(docker_project_root: Path, target_image: DockerTarget) -> str:
    """Gets the python path ENV to use with this project."""
    return "MYPYPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root, target_image=target_image
    )


def get_base_docker_command_for_image(
    non_docker_project_root: Path, docker_project_root: Path, target_image: DockerTarget
) -> list[str]:
    """Basic docker args that are called for every command."""
    return concatenate_args(
        args=[
            "docker",
            "run",
            "--rm",
            f"--workdir={docker_project_root.absolute()}",
            "-e",
            get_python_path_env(
                docker_project_root=docker_project_root, target_image=target_image
            ),
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-v",
            ":".join(
                concatenate_args(
                    args=[
                        non_docker_project_root.absolute(),
                        docker_project_root.absolute(),
                    ]
                )
            ),
        ]
    )


def get_docker_command_for_image(
    non_docker_project_root: Path, docker_project_root: Path, target_image: DockerTarget
) -> list[str]:
    """Basic docker args that are called for dev environment commands."""
    return concatenate_args(
        [
            get_base_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=target_image,
            ),
            get_docker_image_name(
                project_root=docker_project_root, target_image=target_image
            ),
        ]
    )


def get_interactive_docker_command_for_image(
    non_docker_project_root: Path, docker_project_root: Path, target_image: DockerTarget
) -> list[str]:
    """Basic docker args that are called for an interactive dev environment."""
    return concatenate_args(
        args=[
            get_base_docker_command_for_image(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
                target_image=target_image,
            ),
            "-it",
            get_docker_image_name(
                project_root=docker_project_root, target_image=target_image
            ),
        ]
    )


def get_docker_build_command(
    project_root: Path,
    target_image: DockerTarget,
    extra_args: None | dict[str, Any] = None,
) -> list[str]:
    """Creates docker build command."""
    flattened_extra_args = []
    if extra_args is not None:
        for extra_arg_key, extra_arg_val in extra_args.items():
            flattened_extra_args.append(extra_arg_key)
            if extra_arg_val is not None:
                flattened_extra_args.append(extra_arg_val)
    return concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=project_root),
            "--target",
            target_image.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            flattened_extra_args,
            "-t",
            get_docker_image_name(project_root=project_root, target_image=target_image),
            project_root.absolute(),
        ]
    )
