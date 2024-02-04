from pathlib import Path
from typing import Any

import pytest
from build_vars.file_and_dir_path_vars import get_poetry_lock_file, get_pyproject_toml
from build_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
    get_pulumi_version,
    get_pyproject_toml_data,
)


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

    def test_get_project_name(
        self, mock_project_root: Path, mock_local_pyproject_toml_file, project_name: str
    ):
        assert get_project_name(project_root=mock_project_root) == project_name


class TestPoetryLock:
    """A class to hold poetry.lock tests and fixtures."""

    pulumi_versions = ["0.0.0", "0.0.1", "0.1.0", "1.0.0"]
    other_package = '[[package]]\nname = "other_package"\nversion = "1.0.0"\n\n'

    @pytest.fixture(params=pulumi_versions)
    def pulumi_version(self, request) -> str:
        """The version contained in the pyproject toml."""
        return request.param

    @pytest.fixture
    def poetry_lock_contents(self, pulumi_version: str) -> str:
        """The contents of a pyproject toml to be used in testing."""
        return (
            self.other_package
            + f'[[package]]\nname = "pulumi"\nversion = "{pulumi_version}"'
        )

    @pytest.fixture
    def mock_poetry_lock_file(self, poetry_lock_contents, mock_project_root) -> Path:
        """Creates a mock pyproject toml file for use in testing."""
        mock_poetry_lock_file = get_poetry_lock_file(project_root=mock_project_root)
        mock_poetry_lock_file.write_text(poetry_lock_contents)
        return mock_poetry_lock_file

    def test_get_pulumi_version(
        self,
        mock_project_root: Path,
        mock_poetry_lock_file: Path,
        pulumi_version: str,
    ):
        assert get_pulumi_version(project_root=mock_project_root) == pulumi_version

    def test_get_pulumi_version_not_found(self, mock_project_root: Path):
        mock_poetry_lock_file = get_poetry_lock_file(project_root=mock_project_root)
        mock_poetry_lock_file.write_text(self.other_package)
        with pytest.raises(ValueError):
            get_pulumi_version(project_root=mock_project_root)
