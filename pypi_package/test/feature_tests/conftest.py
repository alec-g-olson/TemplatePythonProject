"""Shared fixtures for PYPI feature tests."""

import os
import shutil
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def pypi_package_root_dir() -> Path:
    """Return the root directory of the ``pypi_package`` subproject."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def staged_pypi_package_root(tmp_path: Path, pypi_package_root_dir: Path) -> Path:
    """Create a session-scoped copy of ``pypi_package`` for subprocess tests."""
    staged_root = tmp_path.joinpath("pypi_package")
    shutil.copytree(
        src=pypi_package_root_dir,
        dst=staged_root,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    return staged_root


@pytest.fixture(scope="session")
def staged_pypi_src_dir(staged_pypi_package_root: Path) -> Path:
    """Return the src directory from the staged package copy."""
    return staged_pypi_package_root.joinpath("src")


@pytest.fixture(scope="session")
def staged_main_file(staged_pypi_src_dir: Path) -> Path:
    """Return the staged CLI entrypoint path."""
    return staged_pypi_src_dir.joinpath("template_python_project", "main.py")


@pytest.fixture(scope="session")
def staged_main_command(staged_main_file: Path) -> list[str]:
    """Return the command prefix for running the staged CLI."""
    return [sys.executable, str(staged_main_file)]


@pytest.fixture(scope="session")
def staged_python_env(staged_pypi_src_dir: Path) -> dict[str, str]:
    """Build environment vars so subprocesses import from the staged src path."""
    env = os.environ.copy()
    existing_python_path = env.get("PYTHONPATH")
    staged_src = str(staged_pypi_src_dir)
    env["PYTHONPATH"] = (
        staged_src
        if existing_python_path is None
        else f"{staged_src}{os.pathsep}{existing_python_path}"
    )
    return env
