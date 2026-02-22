"""Utilities for branch-aware feature-test ticket ids and Docker image tags."""

from pathlib import Path
from subprocess import run

from build_support.ci_cd_vars.docker_vars import (
    DockerTarget,
    get_docker_image_name,
    get_docker_tag_suffix,
)
from build_support.ci_cd_vars.git_status_vars import get_ticket_id, \
    current_branch_is_main
from build_support.ci_cd_vars.project_setting_vars import get_project_name


def get_feature_test_ticket_id(project_root: Path, test_ticket_id: str) -> str:
    """Build a test ticket id prefixed with the current branch identifier.

    Args:
        project_root (Path): Root of the project under test.
        test_ticket_id (str): The test-specific ticket/id suffix to append.

    Returns:
        str: ``f"{ticket_id}{test_ticket_id}"`` on non-main branches, otherwise
            ``test_ticket_id``.
    """
    ticket_id = get_ticket_id(project_root=project_root)
    return f"{ticket_id}{test_ticket_id}" if ticket_id is not None else test_ticket_id


def _docker_image_exists(image_name: str) -> bool:
    """Determine whether a Docker image exists locally.

    Args:
        image_name (str): Full Docker image name and tag.

    Returns:
        bool: ``True`` when the image exists locally.
    """
    return (
        run(
            args=["docker", "image", "inspect", image_name],
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def tag_current_branch_images_for_feature_test_ticket_id(
    project_root: Path, ticket_id: str
) -> None:
    """Alias current-branch images to branch-scoped test image names.

    Args:
        project_root (Path): Root of the project under test.
        ticket_id (str): Feature-test ticket id to append as image suffix.

    Returns:
        None
    """
    if current_branch_is_main(project_root=project_root):
        return
    project_name = get_project_name(project_root=project_root)
    current_suffix = get_docker_tag_suffix(project_root=project_root)
    source_and_target_images = [
        (
            get_docker_image_name(
                project_root=project_root, target_image=DockerTarget.BUILD
            ),
            f"{project_name}:build-{ticket_id}",
        ),
        (
            get_docker_image_name(
                project_root=project_root, target_image=DockerTarget.DEV
            ),
            f"{project_name}:dev-{ticket_id}",
        ),
        (
            get_docker_image_name(
                project_root=project_root, target_image=DockerTarget.PROD
            ),
            f"{project_name}:prod-{ticket_id}",
        ),
        (
            f"{project_name}:pulumi{current_suffix}",
            f"{project_name}:pulumi-{ticket_id}",
        ),
    ]
    for source_image, test_image in source_and_target_images:
        if _docker_image_exists(image_name=source_image):
            run(args=["docker", "tag", source_image, test_image], check=True)
