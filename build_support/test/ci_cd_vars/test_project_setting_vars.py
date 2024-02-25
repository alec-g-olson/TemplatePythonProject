from pathlib import Path
from typing import Any

import pytest
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_poetry_lock_file,
    get_pyproject_toml,
)
from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
    get_pulumi_version,
    get_pyproject_toml_data,
    is_dev_project_version,
    is_prod_project_version,
)
from conftest import other_package_info


def test_parse_real_pyproject_toml_file(real_project_root_dir):
    # just test to make sure it is parseable, contents not checked
    get_pyproject_toml_data(project_root=real_project_root_dir)


def test_parse_real_poetry_lock_file(real_project_root_dir):
    # just test to make sure it is parseable, contents not checked
    # replace with generic get_poetry_lock_data when needed
    get_pulumi_version(project_root=real_project_root_dir)


class TestPyprojectToml:
    """A class to hold pyproject toml tests and fixtures."""

    def test_get_pyproject_toml_data(
        self,
        mock_project_root: Path,
        mock_local_pyproject_toml_file,
        pyproject_toml_data: dict[Any, Any],
    ):
        assert (
            get_pyproject_toml_data(project_root=mock_project_root)
            == pyproject_toml_data
        )

    def test_get_project_version(
        self,
        mock_project_root: Path,
        mock_local_pyproject_toml_file,
        project_version: str,
    ):
        assert (
            get_project_version(project_root=mock_project_root) == "v" + project_version
        )

    def test_get_bad_project_version(
        self,
        mock_project_root: Path,
    ):
        mock_pyproject_toml_file = get_pyproject_toml(project_root=mock_project_root)
        mock_pyproject_toml_file.write_text(
            '[tool.poetry]\nname = "some_project_name"\nversion = "AN_INVALID_PROJECT_VERSION"',
        )
        with pytest.raises(ValueError):
            get_project_version(project_root=mock_project_root)

    def test_is_dev_project_version(
        self,
        project_version: str,
    ):
        assert is_dev_project_version(project_version=project_version) == (
            "dev" in project_version
        )

    def test_is_prod_project_version(
        self,
        project_version: str,
    ):
        assert is_prod_project_version(project_version=project_version) == (
            "dev" not in project_version
        )

    def test_get_project_name(
        self,
        mock_project_root: Path,
        mock_local_pyproject_toml_file,
        project_name: str,
    ):
        assert get_project_name(project_root=mock_project_root) == project_name


class TestPoetryLock:
    """A class to hold poetry.lock tests and fixtures."""

    def test_get_pulumi_version(
        self,
        mock_project_root: Path,
        mock_local_poetry_lock_file: Path,
        pulumi_version: str,
    ):
        assert get_pulumi_version(project_root=mock_project_root) == pulumi_version

    def test_get_pulumi_version_not_found(self, docker_project_root: Path):
        mock_poetry_lock_file = get_poetry_lock_file(project_root=docker_project_root)
        mock_poetry_lock_file.write_text(other_package_info)
        with pytest.raises(ValueError):
            get_pulumi_version(project_root=docker_project_root)
