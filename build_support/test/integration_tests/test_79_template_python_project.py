from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)


@pytest.mark.usefixtures("mock_new_branch")
def test_check_integration_test_added(
    mock_project_root: Path, current_ticket_name: str, make_command_prefix: list[str]
) -> None:
    build_support_subproject = get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    )
    project_name = get_project_name(project_root=mock_project_root)
    build_support_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
    ).joinpath(f"test_{current_ticket_name}_{project_name}.py").write_text(
        "def test_something() -> None:\n    assert True\n"
    )
    cmd = Popen(args=(*make_command_prefix, "check_process"), cwd=mock_project_root)
    cmd.communicate()
    assert cmd.returncode == 0


@pytest.mark.usefixtures("mock_new_branch")
def test_fail_check_integration_test_not_added_to_branch(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    cmd = Popen(args=(*make_command_prefix, "check_process"), cwd=mock_project_root)
    cmd.communicate()
    assert cmd.returncode != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_pass_check_integration_test_not_added_to_main(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    cmd = Popen(args=(*make_command_prefix, "check_process"), cwd=mock_project_root)
    cmd.communicate()
    assert cmd.returncode == 0
