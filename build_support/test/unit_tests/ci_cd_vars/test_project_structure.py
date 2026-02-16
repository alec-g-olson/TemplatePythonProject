from pathlib import Path

from build_support.ci_cd_vars.project_structure import (
    get_build_dir,
    get_dockerfile,
    get_docs_dir,
    get_feature_test_log_name,
    get_feature_test_scratch_folder,
    get_license_file,
    get_new_project_settings,
    get_poetry_lock_file,
    get_pyproject_toml,
    get_readme,
    get_sphinx_conf_dir,
    get_test_resource_dir,
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
        project_root=mock_project_root
    ) == mock_project_root.joinpath("pyproject.toml")


def test_get_license_file(mock_project_root: Path) -> None:
    assert get_license_file(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("LICENSE")


def test_get_poetry_lock_file(mock_project_root: Path) -> None:
    assert get_poetry_lock_file(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("poetry.lock")


def test_get_build_dir(mock_project_root: Path) -> None:
    expected_build_dir = mock_project_root.joinpath("build")
    assert not expected_build_dir.exists()
    assert get_build_dir(project_root=mock_project_root) == expected_build_dir
    assert expected_build_dir.exists()


def test_get_feature_test_scratch_folder(mock_project_root: Path) -> None:
    expected_feature_test_scratch_folder = mock_project_root.joinpath(
        "test_scratch_folder"
    )
    assert not expected_feature_test_scratch_folder.exists()
    assert (
        get_feature_test_scratch_folder(project_root=mock_project_root)
        == expected_feature_test_scratch_folder
    )
    assert expected_feature_test_scratch_folder.exists()


def test_get_docs_dir(mock_project_root: Path) -> None:
    expected_docs_dir = mock_project_root.joinpath("docs")
    assert not expected_docs_dir.exists()
    assert get_docs_dir(project_root=mock_project_root) == expected_docs_dir
    assert expected_docs_dir.exists()


def test_get_dockerfile(mock_project_root: Path) -> None:
    assert get_dockerfile(project_root=mock_project_root) == mock_project_root.joinpath(
        "Dockerfile"
    )


def test_get_readme(mock_project_root: Path) -> None:
    assert get_readme(project_root=mock_project_root) == mock_project_root.joinpath(
        "README.md"
    )


def test_get_feature_test_log_name(mock_project_root: Path) -> None:
    test_name = "test_something[param1::param2]"
    expected_log_path = get_feature_test_scratch_folder(
        project_root=mock_project_root
    ).joinpath("test_logs", "test_something_param1_param2.log")
    assert not expected_log_path.parent.exists()
    result = get_feature_test_log_name(
        project_root=mock_project_root, test_name=test_name
    )
    assert result == expected_log_path
    assert expected_log_path.parent.exists()
    # Verify sanitization
    assert "[" not in result.name
    assert "]" not in result.name
    assert "::" not in result.name


def test_get_sphinx_conf_dir(mock_project_root: Path) -> None:
    assert get_sphinx_conf_dir(project_root=mock_project_root) == get_docs_dir(
        project_root=mock_project_root
    ).joinpath("sphinx_conf")


def test_get_new_project_settings(mock_project_root: Path) -> None:
    assert get_new_project_settings(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("new_project_settings.yaml")


def test_get_test_resource_dir() -> None:
    test_file = Path("/a/b/test_foo.py")
    assert get_test_resource_dir(test_file=test_file) == Path("/a/b/test_foo_resources")


def test_get_test_resource_dir_nested() -> None:
    test_file = Path("/project/tests/unit/test_bar.py")
    assert get_test_resource_dir(test_file=test_file) == Path(
        "/project/tests/unit/test_bar_resources"
    )
