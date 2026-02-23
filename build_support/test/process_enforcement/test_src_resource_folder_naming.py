"""Enforce the source resource folder naming convention.

Every non-package, non-cache subdirectory under a source package directory
must follow the ``{src_file_stem}_resources`` naming pattern and have a
corresponding source file next to it.
"""

from pathlib import Path

from build_support.ci_cd_vars.project_structure import get_resource_dir
from build_support.ci_cd_vars.subproject_structure import (
    get_all_python_subprojects_with_src,
)

IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache"}


def _get_non_package_dirs(root: Path) -> list[Path]:
    """Collect all non-package, non-cache directories under *root*.

    A directory is considered a Python package if it contains an
    ``__init__.py`` file. Cache directories (``__pycache__``,
    ``.pytest_cache``) are silently skipped along with their
    children.

    Args:
        root (Path): The top-level directory to walk.

    Returns:
        list[Path]: Sorted list of non-package directories found.
    """
    non_package_dirs: list[Path] = []
    if not root.exists():  # pragma: no cov - not all packages exist
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


def test_all_non_package_src_dirs_follow_resource_naming(
    real_project_root_dir: Path,
) -> None:
    """Assert every non-package source directory follows resource conventions."""
    violations: list[str] = []
    for subproject in get_all_python_subprojects_with_src(
        project_root=real_project_root_dir
    ):
        for non_pkg_dir in _get_non_package_dirs(
            root=subproject.get_python_package_dir()
        ):
            dir_name = non_pkg_dir.name
            if not dir_name.endswith("_resources"):  # pragma: no cov
                violations.append(
                    f"{non_pkg_dir} is not a Python package and "
                    f"does not follow the *_resources naming "
                    f"convention."
                )
                continue
            expected_src_stem = dir_name.removesuffix("_resources")
            expected_src_file = non_pkg_dir.parent / f"{expected_src_stem}.py"
            if not expected_src_file.exists():  # pragma: no cov
                violations.append(
                    f"{non_pkg_dir} has no corresponding source "
                    f"file {expected_src_file}."
                )
                continue
            expected_resource_dir = get_resource_dir(file_path=expected_src_file)
            if non_pkg_dir != expected_resource_dir:  # pragma: no cov
                violations.append(
                    f"{non_pkg_dir} does not match "
                    f"get_resource_dir() output "
                    f"{expected_resource_dir}."
                )
    assert not violations, "\n".join(violations)
