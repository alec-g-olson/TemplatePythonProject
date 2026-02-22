from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo
from build_support.ci_cd_vars.build_paths import get_git_info_yaml
from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_base_docker_command_for_image,
    get_docker_build_command,
    get_docker_command_for_image,
    get_docker_image_name,
    get_docker_tag_suffix,
    get_interactive_docker_command_for_image,
    get_mypy_path_env,
    get_mypy_path_for_target_image,
    get_python_path_env,
    get_python_path_for_target_image,
)
from build_support.ci_cd_vars.file_and_dir_path_vars import (
    get_all_python_folders,
    get_all_src_folders,
    get_test_utils_dirs,
)
from build_support.ci_cd_vars.project_structure import get_dockerfile
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from build_support.process_runner import concatenate_args

docker_targets = list(DockerTarget)
test_project_names = ["test_project_one", "some_other_project"]


@pytest.fixture(params=docker_targets)
def docker_target(request: SubRequest) -> DockerTarget:
    return cast(DockerTarget, request.param)


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_image_name(
    mock_project_root: Path, project_name: str, docker_target: DockerTarget
) -> None:
    assert (
        get_docker_image_name(
            project_root=mock_project_root, target_image=docker_target
        )
        == f"{project_name}:{docker_target.value}"
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_image_name_with_branch_suffix(
    mock_project_root: Path, project_name: str, docker_target: DockerTarget
) -> None:
    with patch(
        "build_support.ci_cd_vars.docker_vars.get_docker_tag_suffix"
    ) as get_docker_tag_suffix_mock:
        get_docker_tag_suffix_mock.return_value = "-TEST001"
        assert (
            get_docker_image_name(
                project_root=mock_project_root, target_image=docker_target
            )
            == f"{project_name}:{docker_target.value}-TEST001"
        )
        get_docker_tag_suffix_mock.assert_called_once_with(
            project_root=mock_project_root
        )


def test_get_docker_tag_suffix_when_git_info_is_missing(
    mock_project_root: Path,
) -> None:
    assert get_docker_tag_suffix(project_root=mock_project_root) == ""


@pytest.mark.parametrize(
    argnames=("branch_name", "expected_suffix"),
    argvalues=[
        (GitInfo.get_primary_branch_name(), ""),
        ("TEST001", "-TEST001"),
        ("TEST001-short-description", "-TEST001"),
        ("101", "-101"),
    ],
)
def test_get_docker_tag_suffix_from_git_info(
    mock_project_root: Path, branch_name: str, expected_suffix: str
) -> None:
    git_info = GitInfo(
        branch=branch_name,
        tags=[],
        modified_subprojects=[],
        dockerfile_modified=False,
        poetry_lock_file_modified=False,
    )
    git_info_yaml_path = get_git_info_yaml(project_root=mock_project_root)
    git_info_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    git_info_yaml_path.write_text(git_info.to_yaml())

    assert get_docker_tag_suffix(project_root=mock_project_root) == expected_suffix


def test_get_python_path_for_target_image(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    observed_python_path = get_python_path_for_target_image(
        docker_project_root=docker_project_root, target_image=docker_target
    )

    if docker_target == DockerTarget.BUILD:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.BUILD_SUPPORT,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    elif docker_target == DockerTarget.DEV:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[get_all_python_folders(project_root=docker_project_root)]
            )
        )
    elif docker_target == DockerTarget.PROD:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.PYPI,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    elif docker_target == DockerTarget.INFRA:
        assert observed_python_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.INFRA,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    else:  # pragma: no cov - will only hit if enum not covered
        msg = f"{docker_target.__name__} is not a supported type."
        raise ValueError(msg)


def test_get_python_path_env(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_python_path_env(
        docker_project_root=docker_project_root, target_image=docker_target
    ) == "PYTHONPATH=" + get_python_path_for_target_image(
        docker_project_root=docker_project_root, target_image=docker_target
    )


def test_get_mypy_path_for_target_image(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    observed_mypy_path = get_mypy_path_for_target_image(
        docker_project_root=docker_project_root, target_image=docker_target
    )

    if docker_target == DockerTarget.BUILD:
        assert observed_mypy_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.BUILD_SUPPORT,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    elif docker_target == DockerTarget.DEV:
        src_folders = get_all_src_folders(project_root=docker_project_root)
        test_utils_dirs = get_test_utils_dirs(project_root=docker_project_root)
        expected_folders = src_folders + test_utils_dirs
        assert observed_mypy_path == ":".join(concatenate_args(args=[expected_folders]))
    elif docker_target == DockerTarget.PROD:
        assert observed_mypy_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.PYPI,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    elif docker_target == DockerTarget.INFRA:
        assert observed_mypy_path == ":".join(
            concatenate_args(
                args=[
                    get_python_subproject(
                        subproject_context=SubprojectContext.INFRA,
                        project_root=docker_project_root,
                    ).get_src_dir()
                ]
            )
        )
    else:  # pragma: no cov - will only hit if enum not covered
        msg = f"{docker_target.__name__} is not a supported type."
        raise ValueError(msg)


def test_get_mypy_path_env(
    docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_mypy_path_env(
        docker_project_root=docker_project_root, target_image=docker_target
    ) == "MYPYPATH=" + get_mypy_path_for_target_image(
        docker_project_root=docker_project_root, target_image=docker_target
    )


def test_get_base_docker_command_for_image(
    mock_project_root: Path, docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_base_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        args=[
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            f"--workdir={docker_project_root.absolute()}",
            "-e",
            get_python_path_env(
                docker_project_root=docker_project_root, target_image=docker_target
            ),
            "-e",
            f"NON_DOCKER_PROJECT_ROOT={mock_project_root.absolute()}",
            "-e",
            f"DOCKER_REMOTE_PROJECT_ROOT={docker_project_root.absolute()}",
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-v",
            ":".join(
                concatenate_args(
                    args=[mock_project_root.absolute(), docker_project_root.absolute()]
                )
            ),
        ]
    )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_get_docker_command_for_image(
    mock_project_root: Path, docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        [
            get_base_docker_command_for_image(
                non_docker_project_root=mock_project_root,
                docker_project_root=docker_project_root,
                target_image=docker_target,
            ),
            get_docker_image_name(
                project_root=docker_project_root, target_image=docker_target
            ),
        ]
    )


@pytest.mark.usefixtures("mock_docker_pyproject_toml_file")
def test_get_interactive_docker_command_for_image(
    mock_project_root: Path, docker_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_interactive_docker_command_for_image(
        non_docker_project_root=mock_project_root,
        docker_project_root=docker_project_root,
        target_image=docker_target,
    ) == concatenate_args(
        [
            get_base_docker_command_for_image(
                non_docker_project_root=mock_project_root,
                docker_project_root=docker_project_root,
                target_image=docker_target,
            ),
            "-it",
            get_docker_image_name(
                project_root=docker_project_root, target_image=docker_target
            ),
        ]
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_build_command_no_extras(
    mock_project_root: Path, docker_target: DockerTarget
) -> None:
    standard = get_docker_build_command(
        docker_project_root=mock_project_root, target_image=docker_target
    )
    no_extra_explicit = get_docker_build_command(
        docker_project_root=mock_project_root,
        target_image=docker_target,
        extra_args=None,
    )
    empty_extra_args = get_docker_build_command(
        docker_project_root=mock_project_root, target_image=docker_target, extra_args={}
    )
    assert standard == no_extra_explicit
    assert standard == empty_extra_args
    assert standard == concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=mock_project_root),
            "--target",
            docker_target.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            [],
            "-t",
            get_docker_image_name(
                project_root=mock_project_root, target_image=docker_target
            ),
            mock_project_root.absolute(),
        ]
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_build_command_with_flat_extras(
    mock_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_docker_build_command(
        docker_project_root=mock_project_root,
        target_image=docker_target,
        extra_args={"--some-key": 8, "--no-val-with-key": None, "--other": "whee"},
    ) == concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=mock_project_root),
            "--target",
            docker_target.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            ["--some-key", "8", "--no-val-with-key", "--other", "whee"],
            "-t",
            get_docker_image_name(
                project_root=mock_project_root, target_image=docker_target
            ),
            mock_project_root.absolute(),
        ]
    )


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_docker_build_command_with_list_extras(
    mock_project_root: Path, docker_target: DockerTarget
) -> None:
    assert get_docker_build_command(
        docker_project_root=mock_project_root,
        target_image=docker_target,
        extra_args={
            "--some-key": [8, 10],
            "--no-val-with-key": None,
            "--other": "whee",
        },
    ) == concatenate_args(
        args=[
            "docker",
            "build",
            "-f",
            get_dockerfile(project_root=mock_project_root),
            "--target",
            docker_target.value,
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            [
                "--some-key",
                "8",
                "--some-key",
                "10",
                "--no-val-with-key",
                "--other",
                "whee",
            ],
            "-t",
            get_docker_image_name(
                project_root=mock_project_root, target_image=docker_target
            ),
            mock_project_root.absolute(),
        ]
    )
