"""Tests to enforce ticketing discipline.

Every feature branch must have a corresponding ticket file in docs/tickets/
that describes the work being done. This ensures all work is tracked,
planned, and documented before implementation.
"""

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from build_support.ci_cd_tasks.env_setup_tasks import GitInfo


class MissingTicketInfo(BaseModel):
    """Information about a missing ticket."""

    branch_name: str
    expected_ticket_path: Path
    message: str


def _extract_ticket_id_from_branch(branch_name: str) -> str | None:
    """Extract the numeric ticket ID from a branch name.

    Branch names follow the pattern: {ticket-id}-{description}
    E.g., "42-add-codon-optimization" → "42"

    Args:
        branch_name (str): The git branch name.

    Returns:
        str | None: The ticket ID, or None if the branch doesn't follow the pattern.
    """
    match = re.match(r"^(\d+)-", branch_name)
    return match.group(1) if match else None


def _is_feature_branch(branch_name: str) -> bool:
    """Determine if a branch is a feature branch requiring a ticket.

    Main, master, and develop branches don't require tickets.
    All other branches are assumed to be feature branches.

    Args:
        branch_name (str): The git branch name.

    Returns:
        bool: True if the branch requires a ticket, False otherwise.
    """
    excluded_branches = {"main", "master", "develop"}
    return branch_name.lower() not in excluded_branches


def _get_expected_ticket_path(
    branch_name: str, tickets_dir: Path
) -> Path | None:
    """Compute the expected ticket file path for a branch.

    Args:
        branch_name (str): The git branch name.
        tickets_dir (Path): The directory where tickets are stored.

    Returns:
        Path | None: The expected path to the ticket file, or None if the
            branch doesn't have a valid ticket ID.
    """
    ticket_id = _extract_ticket_id_from_branch(branch_name)
    if ticket_id is None:
        return None
    # The ticket file name matches the full branch name
    return tickets_dir / f"{branch_name}.rst"


def test_feature_branch_has_ticket(real_git_info: GitInfo, real_project_root_dir: Path) -> None:
    """A feature branch must have a corresponding ticket file.

    Every feature branch (not main, master, or develop) must have a ticket
    file at docs/tickets/{ticket-id}-{description}.rst that documents the
    work being done.
    """
    branch_name = real_git_info.branch
    tickets_dir = real_project_root_dir / "docs" / "tickets"

    # Skip check on main/master/develop branches
    if not _is_feature_branch(branch_name):
        pytest.skip(
            f"Branch '{branch_name}' is a primary branch; no ticket required."
        )

    ticket_path = _get_expected_ticket_path(branch_name, tickets_dir)

    # If the branch doesn't follow the naming convention, fail with a clear message
    if ticket_path is None:
        pytest.fail(
            f"Branch name '{branch_name}' does not follow the pattern "
            f"'{{ticket-id}}-{{description}}'. "
            f"Feature branches must start with a numeric ticket ID."
        )

    # Ticket file must exist
    if not ticket_path.exists():
        pytest.fail(
            f"Ticket file not found: {ticket_path.relative_to(real_project_root_dir)}\n"
            f"Branch '{branch_name}' requires a ticket file documenting the work."
        )


def test_feature_branch_ticket_is_non_empty(
    real_git_info: GitInfo, real_project_root_dir: Path
) -> None:
    """The ticket file must contain meaningful content.

    An empty or nearly-empty ticket file is not acceptable. It must
    describe the work being done.
    """
    branch_name = real_git_info.branch
    tickets_dir = real_project_root_dir / "docs" / "tickets"

    # Skip check on main/master/develop branches
    if not _is_feature_branch(branch_name):
        pytest.skip(
            f"Branch '{branch_name}' is a primary branch; no ticket required."
        )

    ticket_path = _get_expected_ticket_path(branch_name, tickets_dir)

    if ticket_path is None or not ticket_path.exists():
        pytest.skip("Ticket path doesn't exist; skipping content check.")

    content = ticket_path.read_text().strip()
    min_content_length = 100  # Reasonable minimum for meaningful description

    if len(content) < min_content_length:
        pytest.fail(
            f"Ticket file is too short: {ticket_path.relative_to(real_project_root_dir)}\n"
            f"Current length: {len(content)} characters\n"
            f"Minimum required: {min_content_length} characters\n"
            f"The ticket must describe the work being done."
        )
