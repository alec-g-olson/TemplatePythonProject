"""A place to hold tasks and variable used for launching docker."""

from enum import StrEnum
from pathlib import Path
from typing import Any

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.project_structure import get_dockerfile
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args


class DockerTarget(StrEnum):
    """An Enum to track the possible docker targets and images."""

    BUILD = "build"
    DEV = "dev"
    PROD = "prod"
    INFRA = "infra"


def get_docker_image_name(project_root: Path, target_image: DockerTarget) -> str:
    """Gets the docker image name for a target.

    Args:
        project_root (Path): Path to this project's root.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the name of.

    Returns:
        str: The name of the requested docker image.
    """
    return ":".join([get_project_name(project_root=project_root), target_image.value])


def get_python_path_for_target_image(
    docker_project_root: Path, target_image: DockerTarget
) -> str:
    """Gets the python path to use with this project.

    Args:
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the python path for.

    Returns:
        str: The PYTHONPATH for the specified docker image.
    """
    match target_image:
        case DockerTarget.BUILD:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.BUILD_SUPPORT,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case DockerTarget.DEV:
            python_folders = get_all_python_folders(project_root=docker_project_root)
        case DockerTarget.PROD:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.PYPI,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case DockerTarget.INFRA:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.INFRA,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case _:  # pragma: no cov - can't hit if all enums are implemented
            msg = f"{target_image!r} is not a valid enum of DockerType."
            raise ValueError(msg)
    return ":".join(concatenate_args(args=[python_folders]))


def get_python_path_env(docker_project_root: Path, target_image: DockerTarget) -> str:
    """Gets the python path ENV to use with this project.

    Args:
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the python path for.

    Returns:
        str: The PYTHONPATH for the specified docker image in the form on an ENV
            variable that can be used on the command line.
    """
    return "PYTHONPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root, target_image=target_image
    )


def get_mypy_path_for_target_image(
    docker_project_root: Path, target_image: DockerTarget
) -> str:
    """Gets the mypy path to use with this project.

    Args:
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the mypy path for.

    Returns:
        str: The MYPYPATH for the specified docker image.
    """
    match target_image:
        case DockerTarget.BUILD:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.BUILD_SUPPORT,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case DockerTarget.DEV:
            src_folders = get_all_src_folders(project_root=docker_project_root)
            test_folders = get_all_test_folders(project_root=docker_project_root)
            python_folders = src_folders + test_folders
        case DockerTarget.PROD:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.PYPI,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case DockerTarget.INFRA:
            python_folders = [
                get_python_subproject(
                    subproject_context=SubprojectContext.INFRA,
                    project_root=docker_project_root,
                ).get_src_dir()
            ]
        case _:  # pragma: no cov - can't hit if all enums are implemented
            msg = f"{target_image!r} is not a valid enum of DockerType."
            raise ValueError(msg)
    return ":".join(concatenate_args(args=[python_folders]))


def get_mypy_path_env(docker_project_root: Path, target_image: DockerTarget) -> str:
    """Gets the mypy path ENV to use with this project.

    Args:
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the mypy path for.

    Returns:
        str: The MYPYPATH for the specified docker image in the form on an ENV variable
            that can be used on the command line.
    """
    return "MYPYPATH=" + get_mypy_path_for_target_image(
        docker_project_root=docker_project_root, target_image=target_image
    )


def get_base_docker_command_for_image(
    non_docker_project_root: Path, docker_project_root: Path, target_image: DockerTarget
) -> list[str]:
    """Builds a list of arguments for running commands in a docker container.

    Note:
        This list does not contain the name of the container.  This is done so that if
        we want to add additional docker command arguments for specific commands we can
        call this function in conjunction with `get_docker_image_name` to build a
        command for the special circumstances we need.

        If we don't need to use special additional arguments use the
        `get_docker_command_for_image` function instead.

    Args:
        non_docker_project_root (Path): Path to this project's root on the local
            machine.
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting a list of args that will allow us to run docker commands
            for.

    Returns:
        str: A list of arguments that we can use to run a command in the specified
            docker container.
    """
    return concatenate_args(
        args=[
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            f"--workdir={docker_project_root.absolute()}",
            "-e",
            get_python_path_env(
                docker_project_root=docker_project_root, target_image=target_image
            ),
            "-e",
            f"NON_DOCKER_PROJECT_ROOT={non_docker_project_root.absolute()}",
            "-e",
            f"DOCKER_REMOTE_PROJECT_ROOT={docker_project_root.absolute()}",
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
    """Builds a list of arguments for running commands in a docker container.

    Args:
        non_docker_project_root (Path): Path to this project's root on the local
            machine.
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting a list of args that will allow us to run docker commands
            for.

    Returns:
        str: A list of arguments that we can use to run a command in the specified
            docker container.
    """
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
    """Arguments to start an interactive docker shell in the specified image.

    Args:
        non_docker_project_root (Path): Path to this project's root on the local
            machine.
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting a list of args that will allow us to run an interactive
            shell in that image.

    Returns:
        str: A list of arguments that we can use to open an interactive shell in the
            specified docker container.
    """
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
    docker_project_root: Path,
    target_image: DockerTarget,
    extra_args: None | dict[str, Any] = None,
) -> list[str]:
    """Creates docker build command.

    Args:
        docker_project_root (Path): Path to this project's root.
        target_image (DockerTarget): An enum specifying which type of docker image we
            are requesting the name of.
        extra_args (None | dict[str, Any]): Any extra arguments we want to add to the
            build command for a special case.

    Returns:
        str: A list of arguments that we can use to build the specified docker
            container.
    """
    flattened_extra_args = []
    if extra_args is not None:
        for extra_arg_key, extra_arg_vals in extra_args.items():
            if not extra_arg_vals:
                flattened_extra_args.append(extra_arg_key)
            else:
                if not isinstance(extra_arg_vals, list):
                    extra_arg_val_list = [extra_arg_vals]
                else:
                    extra_arg_val_list = extra_arg_vals
                for extra_arg_val in extra_arg_val_list:
                    flattened_extra_args.append(extra_arg_key)
                    flattened_extra_args.append(extra_arg_val)
    return concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=docker_project_root),
            "--target",
            target_image.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            flattened_extra_args,
            "-t",
            get_docker_image_name(
                project_root=docker_project_root, target_image=target_image
            ),
            docker_project_root.absolute(),
        ]
    )
