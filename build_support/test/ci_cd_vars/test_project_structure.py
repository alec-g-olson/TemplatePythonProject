from pathlib import Path

from build_support.ci_cd_vars.project_structure import (
    get_build_dir,
    get_dockerfile,
    get_license_file,
    get_poetry_lock_file,
    get_pyproject_toml,
    maybe_build_dir,
)


def test_maybe_build_dir_new_dir(tmp_path: Path) -> None:
    dir_to_build = tmp_path.joinpath("path", "to", "new", "dir")
    # check dir and parent don't exist
    assert not dir_to_build.exists()
    assert not dir_to_build.parent.exists()
    # check dir is built
    assert maybe_build_dir(dir_to_build=dir_to_build) == dir_to_build
    assert dir_to_build.exists()
    assert dir_to_build.is_dir()
    # check ok if dir exists
    maybe_build_dir(dir_to_build=dir_to_build)


def test_get_pyproject_toml(mock_project_root: Path) -> None:
    assert get_pyproject_toml(
        project_root=mock_project_root,
    ) == mock_project_root.joinpath("pyproject.toml")


def test_get_license_file(mock_project_root: Path) -> None:
    assert get_license_file(
        project_root=mock_project_root,
    ) == mock_project_root.joinpath("LICENSE")


def test_get_poetry_lock_file(mock_project_root: Path) -> None:
    assert get_poetry_lock_file(
        project_root=mock_project_root,
    ) == mock_project_root.joinpath("poetry.lock")


def test_get_build_dir(mock_project_root: Path) -> None:
    expected_build_dir = mock_project_root.joinpath("build")
    assert not expected_build_dir.exists()
    assert get_build_dir(project_root=mock_project_root) == expected_build_dir
    assert expected_build_dir.exists()


def test_get_dockerfile(mock_project_root: Path) -> None:
    assert get_dockerfile(project_root=mock_project_root) == mock_project_root.joinpath(
        "Dockerfile",
    )
