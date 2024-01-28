"""A place to hold tasks and variable used in multiple domains."""

import multiprocessing
import tomllib
from enum import Enum
from pathlib import Path
from typing import Any

from dag_engine import concatenate_args, get_output_of_process

THREADS_AVAILABLE = multiprocessing.cpu_count()


def get_current_branch() -> str:
    """Gets the branch that is currently checked out."""
    return get_output_of_process(
        args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
    )


class DockerTarget(Enum):
    """An Enum to track the possible docker targets and images."""

    BUILD = "build"
    DEV = "dev"
    PROD = "prod"
    PULUMI = "pulumi"


def get_pyproject_toml(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project."""
    return project_root.joinpath("pyproject.toml")


def get_license_file(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project."""
    return project_root.joinpath("LICENSE")


def get_new_project_settings(project_root: Path) -> Path:
    """Get a path to the project_settings.yaml in a project."""
    return project_root.joinpath("build_support", "project_settings.yaml")


def get_pyproject_toml_data(project_root: Path) -> dict[Any, Any]:
    """Get a dict with the contents of the pyproject.toml in a project."""
    return tomllib.loads(get_pyproject_toml(project_root=project_root).read_text())


def get_project_version(project_root: Path) -> str:
    """Gets the project version from the pyproject.toml in a project."""
    return (
        "v"
        + get_pyproject_toml_data(project_root=project_root)["tool"]["poetry"][
            "version"
        ]
    )


def get_poetry_lock_file(project_root: Path) -> Path:
    """Get a path to the poetry.lock file in a project."""
    return project_root.joinpath("poetry.lock")


def get_pulumi_version(project_root: Path) -> str:
    """Get the pulumi version in the poetry.lock file."""
    lock_file = get_poetry_lock_file(project_root=project_root)
    lock_data = tomllib.loads(lock_file.read_text())
    for package in lock_data["package"]:
        if package["name"] == "pulumi":
            return package["version"]
    raise RuntimeError(
        "poetry.lock does not have a pulumi package installed, "
        "or is no longer a toml format."
    )


def get_project_name(project_root: Path) -> str:
    """Gets the project name from the pyproject.toml in a project."""
    return get_pyproject_toml_data(project_root=project_root)["tool"]["poetry"]["name"]


def get_build_dir(project_root: Path) -> Path:
    """Gets the build dir for the project."""
    return project_root.joinpath("build")


def get_build_support_dir(project_root: Path) -> Path:
    """Gets the build_support dir for the project."""
    return project_root.joinpath("build_support")


def get_build_src_dir(project_root: Path) -> Path:
    """Gets the build_src dir for the project."""
    return get_build_support_dir(project_root=project_root).joinpath("build_src")


def get_build_test_dir(project_root: Path) -> Path:
    """Gets the build_src dir for the project."""
    return get_build_support_dir(project_root=project_root).joinpath("build_test")


def get_dist_dir(project_root: Path) -> Path:
    """Gets the build dir for the project."""
    return get_build_dir(project_root=project_root).joinpath("dist")


def get_git_info_json(project_root: Path) -> Path:
    """Gets the location of the git_info.json for the project."""
    return get_build_dir(project_root=project_root).joinpath("git_info.json")


def get_docker_image(project_root: Path, target_image: DockerTarget) -> str:
    """Gets the docker image name for a target."""
    return ":".join([get_project_name(project_root=project_root), target_image.value])


def get_dockerfile(project_root: Path) -> Path:
    """Gets the Dockerfile for the project."""
    return project_root.joinpath("Dockerfile")


def get_build_support_src_and_test(project_root: Path) -> list[str]:
    """Gets both the build_src and build_test dir for the project."""
    return concatenate_args(
        args=[
            get_build_src_dir(project_root=project_root),
            get_build_test_dir(project_root=project_root),
        ]
    )


def get_pypi_src_dir(project_root: Path) -> Path:
    """Gets the PyPi src dir for the project."""
    return project_root.joinpath("src")


def get_pypi_test_dir(project_root: Path) -> Path:
    """Gets the PyPi test dir for the project."""
    return project_root.joinpath("test")


def get_pulumi_dir(project_root: Path) -> Path:
    """Gets the PyPi pulumi dir for the project."""
    return project_root.joinpath("pulumi")


def get_pypi_src_and_test(project_root: Path) -> list[str]:
    """Gets both the PyPi src and test dir for the project."""
    return concatenate_args(
        args=[
            get_pypi_src_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
        ]
    )


def get_all_non_pulumi_python_folders(project_root: Path) -> list[str]:
    """Gets all the non-pulumi python folders in the project."""
    return concatenate_args(
        args=[
            get_build_support_src_and_test(project_root=project_root),
            get_pypi_src_and_test(project_root=project_root),
        ]
    )


def get_all_python_folders(project_root: Path) -> list[str]:
    """Gets all the python folders in the project."""
    return concatenate_args(
        args=[
            get_all_non_pulumi_python_folders(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
        ]
    )


def get_all_src_folders(project_root: Path) -> list[str]:
    """Gets all the python src folders in the project."""
    return concatenate_args(
        args=[
            get_build_src_dir(project_root=project_root),
            get_pypi_src_dir(project_root=project_root),
            get_pulumi_dir(project_root=project_root),
        ]
    )


def get_all_test_folders(project_root: Path) -> list[str]:
    """Gets all the python test folders in the project."""
    return concatenate_args(
        args=[
            get_build_test_dir(project_root=project_root),
            get_pypi_test_dir(project_root=project_root),
        ]
    )


def get_temp_dist_dir(project_root: Path) -> Path:
    """Gets the temporary dist dir for the project."""
    return project_root.joinpath("dist")


def get_python_path_for_target_image(
    docker_project_root: Path, target_image: DockerTarget
) -> str:
    """Gets the python path to use with this project."""
    match target_image:
        case DockerTarget.BUILD:
            python_folders: Path | list[str] = get_build_src_dir(
                project_root=docker_project_root
            )
        case DockerTarget.DEV:
            python_folders = get_all_python_folders(project_root=docker_project_root)
        case DockerTarget.PROD:
            python_folders = get_pypi_src_dir(project_root=docker_project_root)
        case DockerTarget.PULUMI:
            python_folders = get_pulumi_dir(project_root=docker_project_root)
        case _:
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
            get_docker_image(
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
            get_docker_image(
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
            get_docker_image(project_root=project_root, target_image=target_image),
            project_root.absolute(),
        ]
    )
