from pathlib import Path
from subprocess import Popen

import pytest

from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from test_utils.command_runner import run_command_and_save_logs


def _run_type_check_build_support(
    mock_project_root: Path, make_command_prefix: list[str]
) -> int:
    cmd = Popen(
        args=(*make_command_prefix, "type_check_build_support"), cwd=mock_project_root
    )
    cmd.communicate()
    return cmd.returncode


def _write_build_support_test_file(
    mock_project_root: Path, file_name: str, file_contents: str
) -> None:
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.BUILD_SUPPORT,
    ).get_test_dir().joinpath(file_name).write_text(file_contents)


@pytest.mark.usefixtures("mock_lightweight_project")
def test_ty_passes_no_issues(
    mock_project_root: Path, make_command_prefix: list[str]
) -> None:
    assert _run_type_check_build_support(
        mock_project_root=mock_project_root,
        make_command_prefix=make_command_prefix,
    ) == 0


@pytest.mark.usefixtures("mock_lightweight_project")
@pytest.mark.parametrize(
    ("file_name", "file_contents"),
    [
        (
            "test_ty_fails_unknown_name.py",
            """def bad() -> int:
    return missing_name
""",
        ),
        (
            "test_ty_fails_return_type.py",
            """def bad() -> int:
    return "bad-value"
""",
        ),
        (
            "test_ty_fails_argument_type.py",
            """def takes_number(value: int) -> None:
    return

takes_number("bad-value")
""",
        ),
    ],
)
def test_ty_fails_for_type_errors(
    mock_project_root: Path,
    make_command_prefix: list[str],
    file_name: str,
    file_contents: str,
) -> None:
    _write_build_support_test_file(
        mock_project_root=mock_project_root,
        file_name=file_name,
        file_contents=file_contents,
    )
    assert (
        _run_type_check_build_support(
            mock_project_root=mock_project_root,
            make_command_prefix=make_command_prefix,
        )
        != 0
    )
