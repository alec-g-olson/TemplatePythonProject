"""A place to hold tasks and variable used in multiple domains."""

import multiprocessing
import tomllib
from pathlib import Path
from typing import Any

from dag_engine import concatenate_args, get_output_of_process

BRANCH = get_output_of_process(
    args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
)
THREADS_AVAILABLE = multiprocessing.cpu_count()


def get_pyproject_toml(project_root: Path) -> Path:
    """Get a path to the pyproject.toml in a project."""
    return project_root.joinpath("pyproject.toml")


def get_project_settings_json(project_root: Path) -> Path:
    """Get a path to the project_settings.json in a project."""
    return project_root.joinpath("build_support", "project_settings.json")


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


def get_docker_dev_image(project_root: Path) -> str:
    """Gets the dev docker image name."""
    return ":".join([get_project_name(project_root=project_root), "dev"])


def get_docker_prod_image(project_root: Path) -> str:
    """Gets the prod docker image name."""
    return ":".join([get_project_name(project_root=project_root), "prod"])


def get_docker_pulumi_image(project_root: Path) -> str:
    """Gets the pulumi docker image name."""
    return ":".join([get_project_name(project_root=project_root), "pulumi"])


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


def get_python_path(project_root: Path) -> str:
    """Gets the python path to use with this project."""
    return ":".join(str(x) for x in get_all_python_folders(project_root=project_root))


def get_python_path_env(project_root: Path) -> str:
    """Gets the python path ENV to use with this project."""
    return "PYTHONPATH=" + get_python_path(project_root=project_root)


def get_mypy_path_env(project_root: Path) -> str:
    """Gets the python path ENV to use with this project."""
    return "MYPYPATH=" + get_python_path(project_root=project_root)


def get_base_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for every command."""
    return concatenate_args(
        args=[
            "docker",
            "run",
            "--rm",
            f"--workdir={docker_project_root.absolute()}",
            "-e",
            get_python_path_env(project_root=docker_project_root),
            "-v",
            f"{non_docker_project_root.absolute()}:{docker_project_root.absolute()}",
        ]
    )


def get_dev_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for dev environment commands."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            get_docker_dev_image(project_root=docker_project_root),
        ]
    )


def get_interactive_dev_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for an interactive dev environment."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            "-it",
            get_docker_dev_image(project_root=docker_project_root),
        ]
    )


def get_prod_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for prod environment commands."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            get_docker_prod_image(project_root=docker_project_root),
        ]
    )


def get_interactive_prod_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for an interactive prod environment."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            "-it",
            get_docker_prod_image(project_root=docker_project_root),
        ]
    )


def get_pulumi_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for pulumi environment commands."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            get_docker_pulumi_image(project_root=docker_project_root),
        ]
    )


def get_interactive_pulumi_docker_command(
    non_docker_project_root: Path, docker_project_root: Path
) -> list[str]:
    """Basic docker args that are called for an interactive pulumi environment."""
    return concatenate_args(
        [
            get_base_docker_command(
                non_docker_project_root=non_docker_project_root,
                docker_project_root=docker_project_root,
            ),
            "-it",
            get_docker_pulumi_image(project_root=docker_project_root),
        ]
    )
