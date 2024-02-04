from pathlib import Path

from build_vars.file_and_dir_path_vars import (
    get_all_non_pulumi_python_folders,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
    get_build_dir,
    get_build_support_dir,
    get_build_support_src_and_test,
    get_build_support_src_dir,
    get_build_support_test_dir,
    get_dist_dir,
    get_dockerfile,
    get_git_info_yaml,
    get_license_file,
    get_new_project_settings,
    get_poetry_lock_file,
    get_pulumi_dir,
    get_pypi_dir,
    get_pypi_src_and_test,
    get_pypi_src_dir,
    get_pypi_test_dir,
    get_pyproject_toml,
    get_temp_dist_dir,
)
from dag_engine import concatenate_args


def test_get_pyproject_toml(real_project_root_dir):
    assert get_pyproject_toml(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("pyproject.toml")


def test_get_license_file(real_project_root_dir):
    assert get_license_file(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("LICENSE")


def test_get_poetry_lock_file(real_project_root_dir):
    assert get_poetry_lock_file(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("poetry.lock")


def test_get_build_dir(real_project_root_dir):
    assert get_build_dir(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("build")


def test_get_build_support_dir(real_project_root_dir):
    assert get_build_support_dir(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("build_support")


def test_get_dockerfile(real_project_root_dir):
    assert get_dockerfile(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("Dockerfile")


def test_get_pypi_dir(real_project_root_dir):
    assert get_pypi_dir(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("pypi_package")


def test_get_pulumi_dir(real_project_root_dir):
    assert get_pulumi_dir(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("pulumi")


def test_get_new_project_settings(real_project_root_dir):
    assert get_new_project_settings(
        project_root=real_project_root_dir
    ) == get_build_support_dir(project_root=real_project_root_dir).joinpath(
        "project_settings.yaml"
    )


def test_get_build_support_src_dir(real_project_root_dir):
    assert get_build_support_src_dir(
        project_root=real_project_root_dir
    ) == get_build_support_dir(project_root=real_project_root_dir).joinpath("build_src")


def test_get_build_support_test_dir(real_project_root_dir):
    assert get_build_support_test_dir(
        project_root=real_project_root_dir
    ) == get_build_support_dir(project_root=real_project_root_dir).joinpath(
        "build_test"
    )


def test_get_build_support_src_and_test(real_project_root_dir):
    assert get_build_support_src_and_test(
        project_root=real_project_root_dir
    ) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=real_project_root_dir),
            get_build_support_test_dir(project_root=real_project_root_dir),
        ]
    )


def test_get_pypi_src_dir(real_project_root_dir):
    assert get_pypi_src_dir(project_root=real_project_root_dir) == get_pypi_dir(
        project_root=real_project_root_dir
    ).joinpath("src")


def test_get_pypi_test_dir(real_project_root_dir):
    assert get_pypi_test_dir(project_root=real_project_root_dir) == get_pypi_dir(
        project_root=real_project_root_dir
    ).joinpath("test")


def test_get_pypi_src_and_test(real_project_root_dir):
    assert get_pypi_src_and_test(
        project_root=real_project_root_dir
    ) == concatenate_args(
        args=[
            get_pypi_src_dir(project_root=real_project_root_dir),
            get_pypi_test_dir(project_root=real_project_root_dir),
        ]
    )


def test_get_dist_dir(real_project_root_dir):
    assert get_dist_dir(project_root=real_project_root_dir) == get_build_dir(
        project_root=real_project_root_dir
    ).joinpath("dist")


def test_get_git_info_yaml(real_project_root_dir):
    assert get_git_info_yaml(project_root=real_project_root_dir) == get_build_dir(
        project_root=real_project_root_dir
    ).joinpath("git_info.yaml")


def test_get_temp_dist_dir(real_project_root_dir):
    assert get_temp_dist_dir(
        project_root=real_project_root_dir
    ) == real_project_root_dir.joinpath("dist")


def test_get_all_non_pulumi_python_folders(real_project_root_dir):
    assert get_all_non_pulumi_python_folders(
        project_root=real_project_root_dir
    ) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=real_project_root_dir),
            get_build_support_test_dir(project_root=real_project_root_dir),
            get_pypi_src_dir(project_root=real_project_root_dir),
            get_pypi_test_dir(project_root=real_project_root_dir),
        ]
    )


def test_get_all_python_folders(real_project_root_dir):
    assert get_all_python_folders(
        project_root=real_project_root_dir
    ) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=real_project_root_dir),
            get_build_support_test_dir(project_root=real_project_root_dir),
            get_pypi_src_dir(project_root=real_project_root_dir),
            get_pypi_test_dir(project_root=real_project_root_dir),
            get_pulumi_dir(project_root=real_project_root_dir),
        ]
    )


def test_get_all_src_folders(real_project_root_dir):
    assert get_all_src_folders(project_root=real_project_root_dir) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=real_project_root_dir),
            get_pypi_src_dir(project_root=real_project_root_dir),
            get_pulumi_dir(project_root=real_project_root_dir),
        ]
    )


def test_get_all_test_folders(real_project_root_dir):
    assert get_all_test_folders(project_root=real_project_root_dir) == concatenate_args(
        args=[
            get_build_support_test_dir(project_root=real_project_root_dir),
            get_pypi_test_dir(project_root=real_project_root_dir),
        ]
    )
