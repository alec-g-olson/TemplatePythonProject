import re
from pathlib import Path

import pytest
from tomlkit import TOMLDocument

from build_support.ci_cd_vars.project_setting_vars import (
    ALLOWED_VERSION_REGEX,
    get_project_name,
    get_project_version,
    get_pulumi_version,
    get_pyproject_toml_data,
    is_dev_project_version,
    is_prod_project_version,
)
from build_support.ci_cd_vars.project_structure import (
    get_pyproject_toml,
    get_uv_lock_file,
)


def test_parse_real_pyproject_toml_file(real_project_root_dir: Path) -> None:
    # just test to make sure it is parseable, contents not checked
    get_pyproject_toml_data(project_root=real_project_root_dir)


def test_parse_real_uv_lock_file(real_project_root_dir: Path) -> None:
    # just test to make sure it is parseable, contents not checked
    get_pulumi_version(project_root=real_project_root_dir)


class TestPyprojectToml:
    """A class to hold pyproject toml tests and fixtures."""

    @pytest.mark.usefixtures("mock_local_pyproject_toml_file")
    def test_get_pyproject_toml_data(
        self, mock_project_root: Path, pyproject_toml_data: TOMLDocument
    ) -> None:
        assert (
            get_pyproject_toml_data(project_root=mock_project_root)
            == pyproject_toml_data
        )

    @pytest.mark.usefixtures("mock_local_pyproject_toml_file")
    def test_get_project_version(
        self, mock_project_root: Path, project_version: str
    ) -> None:
        assert (
            get_project_version(project_root=mock_project_root) == "v" + project_version
        )

    def test_get_bad_project_version(self, mock_project_root: Path) -> None:
        mock_pyproject_toml_file = get_pyproject_toml(project_root=mock_project_root)
        invalid_version = "AN_INVALID_PROJECT_VERSION"
        mock_pyproject_toml_file.write_text(
            f'[project]\nname = "some_project_name"\nversion = "{invalid_version}"'
        )
        expected_message = (
            "Project version in pyproject.toml must match the regex "
            f"'{ALLOWED_VERSION_REGEX.pattern}', found '{invalid_version}'."
        )
        with pytest.raises(ValueError, match=re.escape(expected_message)):
            get_project_version(project_root=mock_project_root)

    def test_is_dev_project_version(self, project_version: str) -> None:
        assert is_dev_project_version(project_version=project_version) == (
            "dev" in project_version
        )

    def test_is_prod_project_version(self, project_version: str) -> None:
        assert is_prod_project_version(project_version=project_version) == (
            "dev" not in project_version
        )

    @pytest.mark.usefixtures("mock_local_pyproject_toml_file")
    def test_get_project_name(self, mock_project_root: Path, project_name: str) -> None:
        assert get_project_name(project_root=mock_project_root) == project_name


class TestUvLock:
    """A class to hold uv lock tests and fixtures."""

    @pytest.mark.usefixtures("mock_local_uv_lock_file")
    def test_get_pulumi_version(
        self, mock_project_root: Path, pulumi_version: str
    ) -> None:
        assert get_pulumi_version(project_root=mock_project_root) == pulumi_version

    def test_get_pulumi_version_not_found(self, docker_project_root: Path) -> None:
        mock_uv_lock_file = get_uv_lock_file(project_root=docker_project_root)
        mock_uv_lock_file.write_text(
            '[[package]]\nname = "other_package"\nversion = "1.0.0"\n\n'
        )
        expected_message = (
            "uv.lock does not have a pulumi package installed, "
            "or is no longer a toml format."
        )
        with pytest.raises(ValueError, match=expected_message):
            get_pulumi_version(project_root=docker_project_root)
