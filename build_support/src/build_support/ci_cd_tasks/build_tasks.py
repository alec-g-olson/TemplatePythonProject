"""ci_cd_tasks should house all tasks that build artifacts that will be pushed."""

from pathlib import Path

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
from build_support.dag_engine import TaskNode, concatenate_args, run_process


class BuildAll(TaskNode):
    """Task for building all artifacts."""

    def required_tasks(self) -> list[TaskNode]:
        """Lists all "sub-builds" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [BuildPypi(), BuildDocs()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Does nothing.

        Arguments are inherited from subclass.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """


class BuildPypi(TaskNode):
    """Task for building PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build a pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to build Pypi package.
        """
        return [
            TestPypi(),
            TestPythonStyle(),
            BuildProdEnvironment(),
        ]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds PyPi package.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "rm",
                    "-rf",
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "poetry",
                    "build",
                ]
            )
        )
        # Todo: clean this up once a new version of poetry supporting "-o" is released
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=non_docker_project_root,
                        docker_project_root=docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "mv",
                    get_temp_dist_dir(project_root=docker_project_root),
                    get_dist_dir(project_root=docker_project_root),
                ]
            )
        )


def build_docs_for_subproject(
    non_docker_project_root: Path,
    docker_project_root: Path,
    subproject_src_dir: Path,
    docs_src_dir: Path,
    docs_build_dir: Path,
) -> None:
    """Builds the docs for a subproject.

    Args:
        non_docker_project_root (Path): Path to this project's root on the local
                machine.
        docker_project_root (Path): Path to this project's root when running in docker
            containers.
        subproject_src_dir (Path): Path to the subproject's src dir on the dev docker
            container.
        docs_src_dir (Path): Path to the subproject's documentation source directory
            on the dev docker container.
        docs_build_dir (Path): Path to the subproject's documentation build directory
            on the dev docker container.

    Returns:
        None
    """
    run_process(
        args=concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=non_docker_project_root,
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
                docs_src_dir,
                subproject_src_dir,
            ]
        )
    )
    run_process(
        args=concatenate_args(
            [
                get_docker_command_for_image(
                    non_docker_project_root=non_docker_project_root,
                    docker_project_root=docker_project_root,
                    target_image=DockerTarget.DEV,
                ),
                "sphinx-build",
                docs_src_dir,
                docs_build_dir,
                "-c",
                get_sphinx_conf_dir(project_root=docker_project_root),
            ]
        )
    )


class BuildDocs(TaskNode):
    """Task for building the sphinx docs for this project."""

    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build docs.

        Returns:
            list[TaskNode]: A list of tasks required to build documentation.
        """
        return [TestPythonStyle()]

    def run(
        self,
        non_docker_project_root: Path,
        docker_project_root: Path,
        local_user_uid: int,
        local_user_gid: int,
    ) -> None:
        """Builds sphinx docs.

        Args:
            non_docker_project_root (Path): Path to this project's root on the local
                machine.
            docker_project_root (Path): Path to this project's root when running
                in docker containers.
            local_user_uid (int): The local user's users id, used when tasks need to be
                run by the local user.
            local_user_gid (int): The local user's group id, used when tasks need to be
                run by the local user.

        Returns:
            None
        """
        build_docs_for_subproject(
            non_docker_project_root=non_docker_project_root,
            docker_project_root=docker_project_root,
            subproject_src_dir=get_pypi_src_dir(project_root=docker_project_root),
            docs_src_dir=get_pypi_docs_src_dir(project_root=docker_project_root),
            docs_build_dir=get_pypi_docs_build_dir(project_root=docker_project_root),
        )
        build_docs_for_subproject(
            non_docker_project_root=non_docker_project_root,
            docker_project_root=docker_project_root,
            subproject_src_dir=get_build_support_src_dir(
                project_root=docker_project_root
            ),
            docs_src_dir=get_build_support_docs_src_dir(
                project_root=docker_project_root
            ),
            docs_build_dir=get_build_support_docs_build_dir(
                project_root=docker_project_root
            ),
        )
