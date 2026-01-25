from pathlib import Path

from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_test_folders,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
)
from build_support.ci_cd_vars.project_structure import get_sphinx_conf_dir
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_dict,
)


def test_get_all_python_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_python_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
        get_sphinx_conf_dir(project_root=real_project_root_dir),
        subprojects[SubprojectContext.INFRA].get_src_dir(),
        subprojects[SubprojectContext.INFRA].get_test_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_test_dir(),
    ]


def test_get_all_src_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_src_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        subprojects[SubprojectContext.INFRA].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
    ]


def test_get_all_test_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_test_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_test_dir(),
        subprojects[SubprojectContext.INFRA].get_test_dir(),
        subprojects[SubprojectContext.PYPI].get_test_dir(),
    ]


def test_get_all_non_test_folders(real_project_root_dir: Path) -> None:
    subprojects = get_all_python_subprojects_dict(project_root=real_project_root_dir)
    assert get_all_non_test_folders(project_root=real_project_root_dir) == [
        subprojects[SubprojectContext.BUILD_SUPPORT].get_src_dir(),
        get_sphinx_conf_dir(project_root=real_project_root_dir),
        subprojects[SubprojectContext.INFRA].get_src_dir(),
        subprojects[SubprojectContext.PYPI].get_src_dir(),
    ]
