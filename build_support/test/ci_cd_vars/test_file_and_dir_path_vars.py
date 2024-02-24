from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_non_pulumi_python_folders,
    get_all_python_folders,
    get_all_src_folders,
    get_all_test_folders,
    get_build_dir,
    get_build_reports_dir,
    get_build_support_dir,
    get_build_support_src_and_test,
    get_build_support_src_dir,
    get_build_support_test_dir,
    get_dist_dir,
    get_dockerfile,
    get_documentation_tests_dir,
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
    get_sphinx_conf_dir,
    get_temp_dist_dir,
    maybe_build_dir,
)
from build_support.dag_engine import concatenate_args


def test_maybe_build_dir_new_dir(tmp_path):
    dir_to_build = tmp_path.joinpath("path", "to", "new", "dir")
    # check dir and parent don't exist
    assert not dir_to_build.exists() and not dir_to_build.parent.exists()
    # check dir is built
    assert maybe_build_dir(dir_to_build=dir_to_build) == dir_to_build
    assert dir_to_build.exists() and dir_to_build.is_dir()
    # check ok if dir exists
    maybe_build_dir(dir_to_build=dir_to_build)


def test_get_pyproject_toml(mock_project_root):
    assert get_pyproject_toml(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("pyproject.toml")


def test_get_license_file(mock_project_root):
    assert get_license_file(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("LICENSE")


def test_get_poetry_lock_file(mock_project_root):
    assert get_poetry_lock_file(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("poetry.lock")


def test_get_build_dir(mock_project_root):
    expected_build_dir = mock_project_root.joinpath("build")
    assert not expected_build_dir.exists()
    assert get_build_dir(project_root=mock_project_root) == expected_build_dir
    assert expected_build_dir.exists()


def test_get_build_support_dir(mock_project_root):
    assert get_build_support_dir(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("build_support")


def test_get_dockerfile(mock_project_root):
    assert get_dockerfile(project_root=mock_project_root) == mock_project_root.joinpath(
        "Dockerfile"
    )


def test_get_pypi_dir(mock_project_root):
    assert get_pypi_dir(project_root=mock_project_root) == mock_project_root.joinpath(
        "pypi_package"
    )


def test_get_pulumi_dir(mock_project_root):
    assert get_pulumi_dir(project_root=mock_project_root) == mock_project_root.joinpath(
        "pulumi"
    )


def test_get_new_project_settings(mock_project_root):
    assert get_new_project_settings(
        project_root=mock_project_root
    ) == get_build_support_dir(project_root=mock_project_root).joinpath(
        "new_project_settings.yaml"
    )


def test_get_build_support_src_dir(mock_project_root):
    assert get_build_support_src_dir(
        project_root=mock_project_root
    ) == get_build_support_dir(project_root=mock_project_root).joinpath("src")


def test_get_build_support_test_dir(mock_project_root):
    assert get_build_support_test_dir(
        project_root=mock_project_root
    ) == get_build_support_dir(project_root=mock_project_root).joinpath("test")


def test_get_build_support_src_and_test(mock_project_root):
    assert get_build_support_src_and_test(
        project_root=mock_project_root
    ) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=mock_project_root),
            get_build_support_test_dir(project_root=mock_project_root),
        ]
    )


def test_get_pypi_src_dir(mock_project_root):
    assert get_pypi_src_dir(project_root=mock_project_root) == get_pypi_dir(
        project_root=mock_project_root
    ).joinpath("src")


def test_get_pypi_test_dir(mock_project_root):
    assert get_pypi_test_dir(project_root=mock_project_root) == get_pypi_dir(
        project_root=mock_project_root
    ).joinpath("test")


def test_get_pypi_src_and_test(mock_project_root):
    assert get_pypi_src_and_test(project_root=mock_project_root) == concatenate_args(
        args=[
            get_pypi_src_dir(project_root=mock_project_root),
            get_pypi_test_dir(project_root=mock_project_root),
        ]
    )


def test_get_dist_dir(mock_project_root):
    expected_dist_dir = get_build_dir(project_root=mock_project_root).joinpath("dist")
    assert not expected_dist_dir.exists()
    assert get_dist_dir(project_root=mock_project_root) == expected_dist_dir
    assert expected_dist_dir.exists()


def test_get_build_reports_dir(mock_project_root):
    expected_reports_dir = get_build_dir(project_root=mock_project_root).joinpath(
        "reports"
    )
    assert not expected_reports_dir.exists()
    assert get_build_reports_dir(project_root=mock_project_root) == expected_reports_dir
    assert expected_reports_dir.exists()


def test_get_git_info_yaml(mock_project_root):
    assert get_git_info_yaml(project_root=mock_project_root) == get_build_dir(
        project_root=mock_project_root
    ).joinpath("git_info.yaml")


def test_get_temp_dist_dir(mock_project_root):
    expected_temp_dist_dir = mock_project_root.joinpath("dist")
    assert not expected_temp_dist_dir.exists()
    assert get_temp_dist_dir(project_root=mock_project_root) == expected_temp_dist_dir
    assert expected_temp_dist_dir.exists()

    assert get_temp_dist_dir(
        project_root=mock_project_root
    ) == mock_project_root.joinpath("dist")


def test_get_all_non_pulumi_python_folders(mock_project_root):
    assert get_all_non_pulumi_python_folders(
        project_root=mock_project_root
    ) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=mock_project_root),
            get_build_support_test_dir(project_root=mock_project_root),
            get_pypi_src_dir(project_root=mock_project_root),
            get_pypi_test_dir(project_root=mock_project_root),
            get_documentation_tests_dir(project_root=mock_project_root),
        ]
    )


def test_get_all_python_folders(mock_project_root):
    assert get_all_python_folders(project_root=mock_project_root) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=mock_project_root),
            get_build_support_test_dir(project_root=mock_project_root),
            get_pypi_src_dir(project_root=mock_project_root),
            get_pypi_test_dir(project_root=mock_project_root),
            get_documentation_tests_dir(project_root=mock_project_root),
            get_pulumi_dir(project_root=mock_project_root),
            get_sphinx_conf_dir(project_root=mock_project_root),
        ]
    )


def test_get_all_src_folders(mock_project_root):
    assert get_all_src_folders(project_root=mock_project_root) == concatenate_args(
        args=[
            get_build_support_src_dir(project_root=mock_project_root),
            get_pypi_src_dir(project_root=mock_project_root),
            get_pulumi_dir(project_root=mock_project_root),
        ]
    )


def test_get_all_test_folders(mock_project_root):
    assert get_all_test_folders(project_root=mock_project_root) == concatenate_args(
        args=[
            get_build_support_test_dir(project_root=mock_project_root),
            get_pypi_test_dir(project_root=mock_project_root),
            get_documentation_tests_dir(project_root=mock_project_root),
        ]
    )
