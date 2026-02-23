"""Enforce the resource folder naming convention for source and test directories.

Every non-package, non-cache subdirectory under a source package directory or
test suite directory must follow the ``{file_stem}_resources`` naming pattern
and have a corresponding source or test file next to it.

Attributes:
    | IGNORED_DIR_NAMES: Directory names that are silently skipped during traversal.
    | TEST_SUITES_TO_CHECK: Test suites whose directories are scanned for naming
        violations.
"""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_resource_dir
from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    get_all_python_subprojects_with_src,
    get_all_python_subprojects_with_test,
)

IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache"}

TEST_SUITES_TO_CHECK = [
    PythonSubproject.TestSuite.UNIT_TESTS,
    PythonSubproject.TestSuite.FEATURE_TESTS,
]


def _get_non_package_dirs(root: Path) -> list[Path]:
    """Collect all non-package, non-cache directories under *root*.

    A directory is considered a Python package if it contains an
    ``__init__.py`` file. Cache directories listed in ``IGNORED_DIR_NAMES``
    are silently skipped along with their children.

    Args:
        root (Path): The top-level directory to walk.

    Returns:
        list[Path]: Sorted list of non-package directories found.
    """
    non_package_dirs: list[Path] = []
    if not root.exists():  # pragma: no cov - not all roots exist
        return non_package_dirs
    dirs_to_visit = [root]
    while dirs_to_visit:
        current = dirs_to_visit.pop()
        for child in sorted(current.iterdir()):
            if child.is_dir():
                if child.name in IGNORED_DIR_NAMES:
                    continue
                if child.joinpath("__init__.py").exists():
                    dirs_to_visit.append(child)
                else:
                    non_package_dirs.append(child)
    return sorted(non_package_dirs)


def _check_resource_dirs(non_package_dirs: list[Path], file_kind: str) -> list[str]:
    """Validate that non-package directories follow the resource naming convention.

    Args:
        non_package_dirs (list[Path]): Non-package directories to validate.
        file_kind (str): Label for violation messages (e.g. ``"source"`` or
            ``"test"``).

    Returns:
        list[str]: A list of violation descriptions; empty when all directories
            conform.
    """
    violations: list[str] = []
    for non_pkg_dir in non_package_dirs:
        dir_name = non_pkg_dir.name
        if not dir_name.endswith("_resources"):  # pragma: no cov
            violations.append(
                f"{non_pkg_dir} is not a Python package and "
                f"does not follow the *_resources naming "
                f"convention."
            )
            continue
        expected_stem = dir_name.removesuffix("_resources")
        expected_file = non_pkg_dir.parent / f"{expected_stem}.py"
        if not expected_file.exists():  # pragma: no cov
            violations.append(
                f"{non_pkg_dir} has no corresponding {file_kind} file {expected_file}."
            )
            continue
        expected_resource_dir = get_resource_dir(file_path=expected_file)
        if non_pkg_dir != expected_resource_dir:  # pragma: no cov
            violations.append(
                f"{non_pkg_dir} does not match "
                f"get_resource_dir() output "
                f"{expected_resource_dir}."
            )
    return violations


def test_all_non_package_src_dirs_follow_resource_naming(
    real_project_root_dir: Path,
) -> None:
    """Assert every non-package source directory follows resource conventions."""
    violations: list[str] = []
    for subproject in get_all_python_subprojects_with_src(
        project_root=real_project_root_dir
    ):
        violations.extend(
            _check_resource_dirs(
                non_package_dirs=_get_non_package_dirs(
                    root=subproject.get_python_package_dir()
                ),
                file_kind="source",
            )
        )
    assert not violations, "\n".join(violations)


def test_all_non_package_test_dirs_follow_resource_naming(
    real_project_root_dir: Path,
) -> None:
    """Assert every non-package test directory follows the resource convention.

    For each non-package, non-cache directory found under a test suite
    directory:

    1. Its name must end with ``_resources``.
    2. The corresponding test file (``{name_without_resources}.py``)
       must exist in the same parent directory.
    3. The directory name must equal
       ``get_resource_dir(file_path=test_file).name`` for that test file.
    """
    violations: list[str] = []
    for subproject in get_all_python_subprojects_with_test(
        project_root=real_project_root_dir
    ):
        for test_suite in TEST_SUITES_TO_CHECK:
            suite_dir = subproject.get_test_suite_dir(test_suite=test_suite)
            violations.extend(
                _check_resource_dirs(
                    non_package_dirs=_get_non_package_dirs(root=suite_dir),
                    file_kind="test",
                )
            )
    assert not violations, "\n".join(violations)
