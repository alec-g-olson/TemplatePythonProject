"""Defines the structure of a python subproject."""

from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_build_dir, maybe_build_dir


class SubprojectContext(Enum):
    """An Enum to track the possible docker targets and images."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    PULUMI = "pulumi"
    DOCUMENTATION_ENFORCEMENT = "process_and_style_enforcement"
    ALL = "all"


@dataclass(frozen=True)
class PythonSubProject:
    """Class that describes a python subproject."""

    project_root: Path
    subproject_name: str

    def get_subproject_build_dir(self) -> Path:
        """Gets and possibly builds a directory in the build folder for this subproject.

        Returns:
            Path: Path to the build dir for this subproject.
        """
        return maybe_build_dir(
            get_build_dir(project_root=self.project_root).joinpath(self.subproject_name)
        )

    def get_subproject_reports_dir(self) -> Path:
        """Gets and possibly builds a dir for storing the subproject build reports.

        Returns:
            Path: Path to the subproject's reports directory.
        """
        return maybe_build_dir(self.get_subproject_build_dir().joinpath("reports"))

    def get_subproject_docs_build_dir(self) -> Path:
        """Gets and possibly builds a dir for building the subproject docs.

        Returns:
            Path: Path to the subproject's docs build directory.
        """
        return maybe_build_dir(self.get_subproject_build_dir().joinpath("docs_build"))

    def get_subproject_docs_source_dir(self) -> Path:
        """Gets and possibly builds a dir for the subproject's docs sources.

        This dir will have its contents copied in from the subproject's docs folder
        from the subproject's root directory.  This allows for us to store the docs
        in a safe place and keep all of our build processes in the build folder.

        Returns:
            Path: Path to the subproject's docs source directory.
        """
        return maybe_build_dir(self.get_subproject_build_dir().joinpath("docs_source"))

    def get_subproject_root(self) -> Path:
        """Gets the root of the python subproject.

        Returns:
            Path: Path to the root of the python subproject.
        """
        return self.project_root.joinpath(self.subproject_name)

    def get_subproject_src_dir(self) -> Path:
        """Gets the src folder in a subproject.

        Returns:
            Path: Path to the src folder in the subproject.
        """
        return self.get_subproject_root().joinpath("src")

    def get_subproject_test_dir(self) -> Path:
        """Gets the test folder in a subproject.

        Returns:
            Path: Path to the test folder in the subproject.
        """
        return self.get_subproject_root().joinpath("test")

    def get_subproject_src_and_test_dir(self) -> list[Path]:
        """Gets the src and test dirs for the subproject.

        Returns:
            list[path]: Path to the build_support src and test dirs for the project.
        """
        return [self.get_subproject_src_dir(), self.get_subproject_test_dir()]

    def get_subproject_docs_dir(self) -> Path:
        """Gets the documents folder in a subproject.

        This dir will have its contents copied to the subproject's docs source build
         folder in the project's build directory.  This allows for us to store the docs
        in a safe place and keep all of our build processes in the build folder.

        Returns:
            Path: Path to the docs folder in the subproject.
        """
        return self.get_subproject_root().joinpath("docs")


@cache
def get_python_subproject(
    subproject_context: SubprojectContext, project_root: Path
) -> PythonSubProject:
    """Gets a Python subproject.

    Args:
        subproject_context: An Enum specifying which python subproject to get.
        project_root: The root directory of the project.

    Returns:
        PythonSubProject: A dataclass that dictates the structure a python subproject.
    """
    if subproject_context == SubprojectContext.ALL:
        name = subproject_context.value
        msg = f"There is no Python subproject for the {name} subproject."
        raise ValueError(msg)
    return PythonSubProject(
        project_root=project_root, subproject_name=subproject_context.value
    )


@cache
def get_all_python_subprojects_dict(
    project_root: Path,
) -> dict[SubprojectContext, PythonSubProject]:
    """Gets all Python subprojects in a dict.

    Args:
        project_root: The root directory of the project.

    Returns:
        dict[SubprojectContext, PythonSubProject]: A dict of all Python subprojects
        using their SubprojectContext as a key.
    """
    return {
        subproject_context: PythonSubProject(
            project_root=project_root, subproject_name=subproject_context.value
        )
        for subproject_context in SubprojectContext
        if subproject_context != SubprojectContext.ALL
    }
