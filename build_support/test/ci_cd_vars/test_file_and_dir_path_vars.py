from pathlib import Path

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_pulumi_python_folders,
    get_all_non_test_folders,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
    get_dist_dir,
    get_git_info_yaml,
    get_license_templates_dir,
    get_new_project_settings,
    get_sphinx_conf_dir,
)
from build_support.ci_cd_vars.project_structure import get_build_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_dict,
    get_python_subproject,
)


def test_get_sphinx_conf_dir(mock_project_root: Path) -> None:
    expected_process_and_style_dir = get_python_subproject(
        subproject_context=SubprojectContext.DOCUMENTATION_ENFORCEMENT,
        project_root=mock_project_root,
    ).get_root_dir()
    expected_sphinx_conf_dir = expected_process_and_style_dir.joinpath("sphinx_conf")
    assert (
        get_sphinx_conf_dir(project_root=mock_project_root) == expected_sphinx_conf_dir
    )


def test_get_new_project_settings(mock_project_root: Path) -> None:
    build_support_dir = get_python_subproject(
        subproject_context=SubprojectContext.BUILD_SUPPORT,
        project_root=mock_project_root,
    ).get_root_dir()
    assert get_new_project_settings(
        project_root=mock_project_root
    ) == build_support_dir.joinpath("new_project_settings.yaml")


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


def test_get_git_info_yaml(mock_project_root: Path) -> None:
    assert get_git_info_yaml(project_root=mock_project_root) == get_build_dir(
        project_root=mock_project_root,
    ).joinpath("git_info.yaml")


def test_get_all_python_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_python_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
        get_sphinx_conf_dir(project_root=real_project_root_dir),
        subprojects[SubprojectContext.DOCUMENTATION_ENFORCEMENT].get_test_dir(),
        subprojects[SubprojectContext.PULUMI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_test_dir(),
    ]


def test_get_all_non_pulumi_python_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_non_pulumi_python_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
        get_sphinx_conf_dir(project_root=real_project_root_dir),
        subprojects[SubprojectContext.DOCUMENTATION_ENFORCEMENT].get_test_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_test_dir(),
    ]


def test_get_all_src_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_src_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        subprojects[SubprojectContext.PULUMI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
    ]


def test_get_all_test_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_test_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
        subprojects[SubprojectContext.DOCUMENTATION_ENFORCEMENT].get_test_dir(),
        subprojects[SubprojectContext.PYPI].get_test_dir(),
    ]


def test_get_all_non_test_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_non_test_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        get_sphinx_conf_dir(project_root=real_project_root_dir),
        subprojects[SubprojectContext.PULUMI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
    ]
