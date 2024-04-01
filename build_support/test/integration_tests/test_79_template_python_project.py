from pathlib import Path

import pytest

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    get_all_python_subprojects_with_test,
)


def build_skeleton_project_at(tmp_project_root: Path) -> None:
    for subproject in get_all_python_subprojects_with_test(
        project_root=tmp_project_root
    ):
        integration_tests = subproject.get_test_suite_dir(
            test_suite=PythonSubproject.TestSuite.INTEGRATION_TESTS
        )
        integration_tests.mkdir(parents=True)


def test_check_integration_test_added(mock_lightweight_project: Path) -> None:
    pytest.fail(f"Write the test{mock_lightweight_project}")
