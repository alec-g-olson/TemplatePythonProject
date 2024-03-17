from pathlib import Path

from build_support.ci_cd_vars.subproject_structure import (
    get_all_python_subprojects_dict,
)


def test_foo(real_project_root_dir: Path) -> None:
    assert len(get_all_python_subprojects_dict(project_root=real_project_root_dir)) > 0
