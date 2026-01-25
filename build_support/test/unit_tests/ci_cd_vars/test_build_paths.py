from pathlib import Path

from build_support.ci_cd_vars.build_paths import (
    get_build_docs_build_dir,
    get_build_docs_dir,
    get_build_docs_source_dir,
    get_build_runtime_report_path,
    get_dist_dir,
    get_git_info_yaml,
    get_license_templates_dir,
    get_local_info_yaml,
)
from build_support.ci_cd_vars.project_structure import get_build_dir


def test_get_dist_dir(mock_project_root: Path) -> None:
    expected_dist_dir = get_build_dir(project_root=mock_project_root).joinpath("dist")
    assert not expected_dist_dir.exists()
    assert get_dist_dir(project_root=mock_project_root) == expected_dist_dir
    assert expected_dist_dir.exists()


def test_get_license_templates_dir(mock_project_root: Path) -> None:
    expected_license_template_dir = get_build_dir(
        project_root=mock_project_root
    ).joinpath("license_templates")
    assert not expected_license_template_dir.exists()
    assert (
        get_license_templates_dir(project_root=mock_project_root)
        == expected_license_template_dir
    )
    assert expected_license_template_dir.exists()


def test_get_local_info_yaml(mock_project_root: Path) -> None:
    assert get_local_info_yaml(project_root=mock_project_root) == get_build_dir(
        project_root=mock_project_root
    ).joinpath("local_info.yaml")


def test_get_git_info_yaml(mock_project_root: Path) -> None:
    assert get_git_info_yaml(project_root=mock_project_root) == get_build_dir(
        project_root=mock_project_root
    ).joinpath("git_info.yaml")


def test_get_build_docs_dir(mock_project_root: Path) -> None:
    expected_build_docs_dir = get_build_dir(project_root=mock_project_root).joinpath(
        "docs"
    )
    assert not expected_build_docs_dir.exists()
    assert get_build_docs_dir(project_root=mock_project_root) == expected_build_docs_dir
    assert expected_build_docs_dir.exists()


def test_get_build_docs_source_dir(mock_project_root: Path) -> None:
    expected_build_docs_source_dir = get_build_docs_dir(
        project_root=mock_project_root
    ).joinpath("source")
    assert not expected_build_docs_source_dir.exists()
    assert (
        get_build_docs_source_dir(project_root=mock_project_root)
        == expected_build_docs_source_dir
    )
    assert expected_build_docs_source_dir.exists()


def test_get_build_docs_build_dir(mock_project_root: Path) -> None:
    expected_build_docs_build_dir = get_build_docs_dir(
        project_root=mock_project_root
    ).joinpath("build")
    assert not expected_build_docs_build_dir.exists()
    assert (
        get_build_docs_build_dir(project_root=mock_project_root)
        == expected_build_docs_build_dir
    )
    assert expected_build_docs_build_dir.exists()


def test_get_build_runtime_report_path(mock_project_root: Path) -> None:
    expected_build_runtime_report_path = get_build_dir(
        project_root=mock_project_root
    ).joinpath("build_runtime.yaml")
    assert (
        get_build_runtime_report_path(project_root=mock_project_root)
        == expected_build_runtime_report_path
    )
