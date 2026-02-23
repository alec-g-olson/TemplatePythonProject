"""Feature tests for ticket 98: switch static typing from mypy to ty.

Verifies that type checking uses ty, succeeds on the repository, and that
pyproject.toml is configured for ty with no mypy configuration.
"""

from pathlib import Path
from typing import Any, cast

import pytest
from _pytest.fixtures import SubRequest
from test_utils.command_runner import run_command_and_save_logs

from build_support.ci_cd_vars.project_setting_vars import get_pyproject_toml_data


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_type_checks_use_ty_and_succeed(
    mock_project_root: Path,
    make_command_prefix: list[str],
    real_project_root_dir: Path,
    request: SubRequest,
) -> None:
    """Running make type_checks uses ty and succeeds on the repository."""
    return_code, _, _ = run_command_and_save_logs(
        args=[*make_command_prefix, "type_checks"],
        cwd=mock_project_root,
        test_name=request.node.name,
        real_project_root_dir=real_project_root_dir,
    )
    assert return_code == 0


def test_pyproject_has_ty_config_and_no_mypy(real_project_root_dir: Path) -> None:
    """pyproject.toml contains ty configuration with all checks at error and no mypy."""
    pyproject_data = get_pyproject_toml_data(project_root=real_project_root_dir)
    tool = cast(dict[str, Any], pyproject_data).get("tool")
    assert tool is not None
    assert "ty" in tool
    ty_config = tool["ty"]
    assert "rules" in ty_config
    assert ty_config["rules"].get("all") == "error"
    assert "mypy" not in tool
