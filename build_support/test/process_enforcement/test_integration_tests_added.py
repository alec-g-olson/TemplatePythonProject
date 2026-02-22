from pathlib import Path

from build_support.ci_cd_vars.git_status_vars import get_current_branch_ticket_id
from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    get_all_python_subprojects_with_test,
)


def test_feature_tests_exist_for_ticket(
    is_on_main: bool, real_project_root_dir: Path
) -> None:
    if not is_on_main:  # pragma: no cov might be on main
        project_name = get_project_name(project_root=real_project_root_dir)
        ticket_id = get_current_branch_ticket_id(project_root=real_project_root_dir)
        test_name = f"test_{ticket_id}_{project_name}.py"
        test_file = next(
            (
                test_file
                for subproject in get_all_python_subprojects_with_test(
                    project_root=real_project_root_dir
                )
                for test_file in subproject.get_test_suite_dir(
                    test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
                ).rglob("*")
                if test_file.name == test_name
            ),
            None,
        )
        assert test_file
        assert any("def test_" in line for line in test_file.read_text().splitlines())
