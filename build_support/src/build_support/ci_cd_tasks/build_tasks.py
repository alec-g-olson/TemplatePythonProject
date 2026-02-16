"""ci_cd_tasks should house all tasks that build artifacts that will be pushed."""

from shutil import copytree
from typing import override

from build_support.ci_cd_tasks.env_setup_tasks import SetupProdEnvironment
from build_support.ci_cd_tasks.task_node import TaskNode
from build_support.ci_cd_tasks.validation_tasks import (
    SubprojectUnitTests,
    ValidatePythonStyle,
)
from build_support.ci_cd_vars.build_paths import (
    get_build_docs_build_dir,
    get_build_docs_source_dir,
    get_dist_dir,
)
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_command_for_image,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
)
from build_support.ci_cd_vars.project_structure import get_docs_dir, get_sphinx_conf_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_with_src,
)
from build_support.process_runner import concatenate_args, run_process


class BuildAll(TaskNode):
    """Task for building all artifacts."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Lists all "sub-builds" to add to the DAG.

        Returns:
            list[TaskNode]: A list of all build tasks.
        """
        return [
            BuildPypi(basic_task_info=self.get_basic_task_info()),
            BuildDocs(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Does nothing.

        Arguments are inherited from subclass.

        Returns:
            None
        """


class BuildPypi(TaskNode):
    """Task for building PyPi package."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build a pypi package.

        Returns:
            list[TaskNode]: A list of tasks required to build Pypi package.
        """
        return [
            SubprojectUnitTests(
                basic_task_info=self.get_basic_task_info(),
                subproject_context=SubprojectContext.PYPI,
            ),
            ValidatePythonStyle(basic_task_info=self.get_basic_task_info()),
            SetupProdEnvironment(basic_task_info=self.get_basic_task_info()),
        ]

    @override
    def run(self) -> None:
        """Builds PyPi package.

        Returns:
            None
        """
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "rm",
                    "-rf",
                    get_dist_dir(project_root=self.docker_project_root),
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.PROD,
                    ),
                    "poetry",
                    "build",
                    "--output",
                    get_dist_dir(project_root=self.docker_project_root),
                ]
            )
        )


class BuildDocs(TaskNode):
    """Task for building the sphinx docs for this project."""

    @override
    def required_tasks(self) -> list[TaskNode]:
        """Get the list of task that need to be run before we can build docs.

        Returns:
            list[TaskNode]: A list of tasks required to build documentation.
        """
        return [ValidatePythonStyle(basic_task_info=self.get_basic_task_info())]

    @override
    def run(self) -> None:
        """Builds sphinx docs.

        Returns:
            None
        """
        subprojects_with_docs = get_all_python_subprojects_with_src(
            project_root=self.docker_project_root
        )
        copytree(
            src=get_docs_dir(project_root=self.docker_project_root),
            dst=get_build_docs_source_dir(project_root=self.docker_project_root),
            dirs_exist_ok=True,
        )
        for subproject in subprojects_with_docs:
            run_process(
                args=concatenate_args(
                    [
                        get_docker_command_for_image(
                            non_docker_project_root=self.non_docker_project_root,
                            docker_project_root=self.docker_project_root,
                            target_image=DockerTarget.DEV,
                        ),
                        "sphinx-apidoc",
                        "-f",
                        "--separate",
                        "--module-first",
                        "--no-toc",
                        "-H",
                        get_project_name(project_root=self.docker_project_root),
                        "-V",
                        get_project_version(project_root=self.docker_project_root),
                        "-o",
                        get_build_docs_source_dir(
                            project_root=self.docker_project_root
                        ),
                        subproject.get_src_dir(),
                    ]
                )
            )
        run_process(
            args=concatenate_args(
                [
                    get_docker_command_for_image(
                        non_docker_project_root=self.non_docker_project_root,
                        docker_project_root=self.docker_project_root,
                        target_image=DockerTarget.DEV,
                    ),
                    "sphinx-build",
                    get_build_docs_source_dir(project_root=self.docker_project_root),
                    get_build_docs_build_dir(project_root=self.docker_project_root),
                    "-c",
                    get_sphinx_conf_dir(project_root=self.docker_project_root),
                ]
            )
        )
