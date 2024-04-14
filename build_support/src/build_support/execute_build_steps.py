"""The entry point into running build tools.

Attributes:
    | CLI_ARG_TO_TASK: A dictionary of the CLI arg to the corresponding task to run.
"""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path

from build_support.ci_cd_tasks.build_tasks import (
    BuildAll,
    BuildDocs,
    BuildPypi,
)
from build_support.ci_cd_tasks.env_setup_tasks import (
    Clean,
    SetupDevEnvironment,
    SetupInfraEnvironment,
    SetupProdEnvironment,
)
from build_support.ci_cd_tasks.lint_tasks import (
    ApplyRuffFixUnsafe,
    Lint,
    RuffFixSafe,
)
from build_support.ci_cd_tasks.push_tasks import PushAll, PushPypi
from build_support.ci_cd_tasks.task_node import (
    BasicTaskInfo,
    PerSubprojectTask,
    TaskNode,
)
from build_support.ci_cd_tasks.validation_tasks import (
    EnforceProcess,
    SubprojectUnitTests,
    ValidateAll,
    ValidatePythonStyle,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import get_local_info_yaml
from build_support.ci_cd_vars.subproject_structure import SubprojectContext
from build_support.dag_engine import run_tasks
from build_support.new_project_setup.setup_new_project import MakeProjectFromTemplate
from build_support.process_runner import ProcessVerbosity, concatenate_args, run_process


@dataclass(frozen=True)
class CliTaskInfo:
    """Dataclass that stores information needed to build a task from a CLI arg."""

    task_node: type[TaskNode]
    subproject_context: SubprojectContext | None = None

    def get_task_node(
        self,
        basic_task_info: BasicTaskInfo,
    ) -> TaskNode:
        """Builds a task node based on the contents of this dataclass.

        Args:
            basic_task_info (BasicTaskInfo): The information required to set up a task.

        Returns:
            TaskNode: The task node based on the contents of this dataclass.

        """
        if self.subproject_context and issubclass(self.task_node, PerSubprojectTask):
            return self.task_node(
                basic_task_info=basic_task_info,
                subproject_context=self.subproject_context,
            )

        if self.subproject_context is None and not issubclass(
            self.task_node, PerSubprojectTask
        ):
            return self.task_node(basic_task_info=basic_task_info)

        subproject_name = (
            self.subproject_context.name if self.subproject_context else "None"
        )
        msg = (
            "Incoherent CLI Task Info.\n"
            f"\ttask_node: {self.task_node.__name__}\n"
            f"\tsubproject_context: {subproject_name}"
        )
        raise ValueError(msg)


#######################################################################################
# Test tasks use the word "Validate" instead of "Test" in their name to prevent
# pytest from getting confused and producing lots of warnings.  However, for the sake
# of standardization and usability we will use "test" instead of "validate" for the
# exposed CLI options and Makefile commands.
#######################################################################################


CLI_ARG_TO_TASK: dict[str, CliTaskInfo] = {
    "make_new_project": CliTaskInfo(task_node=MakeProjectFromTemplate),
    "clean": CliTaskInfo(task_node=Clean),
    "setup_dev_env": CliTaskInfo(task_node=SetupDevEnvironment),
    "setup_prod_env": CliTaskInfo(task_node=SetupProdEnvironment),
    "setup_infra_env": CliTaskInfo(task_node=SetupInfraEnvironment),
    "test_style": CliTaskInfo(task_node=ValidatePythonStyle),
    "check_process": CliTaskInfo(task_node=EnforceProcess),
    "test_build_support": CliTaskInfo(
        task_node=SubprojectUnitTests,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    ),
    "test_pypi": CliTaskInfo(
        task_node=SubprojectUnitTests, subproject_context=SubprojectContext.PYPI
    ),
    "test": CliTaskInfo(task_node=ValidateAll),
    "lint": CliTaskInfo(task_node=Lint),
    "ruff_fix_safe": CliTaskInfo(task_node=RuffFixSafe),
    "apply_unsafe_ruff_fixes": CliTaskInfo(task_node=ApplyRuffFixUnsafe),
    "build_docs": CliTaskInfo(task_node=BuildDocs),
    "build_pypi": CliTaskInfo(task_node=BuildPypi),
    "build": CliTaskInfo(task_node=BuildAll),
    "push_pypi": CliTaskInfo(task_node=PushPypi),
    "push": CliTaskInfo(task_node=PushAll),
}


def fix_permissions(local_user_uid: int, local_user_gid: int) -> None:
    """Resets all file ownership to the local user after running processes.

    Args:
        local_user_uid (int): The user's OS user ID.
        local_user_gid (int): The user's OS group ID.

    Returns:
        None
    """
    local_user = f"{local_user_uid}:{local_user_gid}"
    run_process(
        args=concatenate_args(
            args=[
                "chown",
                "-R",
                local_user,
                [
                    path.absolute()
                    for path in Path(__file__).parent.parent.parent.parent.glob("*")
                    if path.name not in [".git", "test_scratch_folder"]
                ],
            ],
        ),
        verbosity=ProcessVerbosity.SILENT,
    )


def parse_args(args: list[str] | None = None) -> Namespace:
    """Parses arguments from list given or the command line.

    Args:
        args (list[str] | None): Args to parse.  Defaults to None, causing
            sys.argv[1:] to be used.

    Returns:
        Namespace: A namespace made from the parsed args.
    """
    parser = ArgumentParser(
        prog="ExecuteBuildSteps",
        description="This tool exists to facilitate building, testing, "
        "and deploying this project's artifacts",
    )
    parser.add_argument(
        "build_tasks",
        type=str,
        nargs="+",
        help="Build tasks to run.",
        choices=CLI_ARG_TO_TASK.keys(),
    )
    parser.add_argument(
        "--docker-project-root",
        type=Path,
        required=True,
        help="Path to project root on docker machines, used to mount project "
        "when launching docker containers.",
    )
    return parser.parse_args(args=args)


def run_main(args: Namespace) -> None:
    """Runs the logic for the execute_build_steps main.

    Args:
        args (Namespace): A namespace generated by an ArgumentParser.

    Returns:
        None
    """
    local_info_yaml = get_local_info_yaml(project_root=args.docker_project_root)
    basic_task_info = BasicTaskInfo.from_yaml(local_info_yaml.read_text())
    print(basic_task_info.to_yaml())
    requested_tasks = [
        CLI_ARG_TO_TASK[arg].get_task_node(basic_task_info=basic_task_info)
        for arg in args.build_tasks
    ]
    try:
        run_tasks(tasks=requested_tasks)
    except Exception as e:
        print(e)  # noqa: T201
    finally:
        fix_permissions(
            local_user_uid=basic_task_info.local_uid,
            local_user_gid=basic_task_info.local_gid,
        )


if __name__ == "__main__":  # pragma: no cover - main
    run_main(args=parse_args())
