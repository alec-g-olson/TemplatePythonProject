"""Feature tests for ticket 85: static type checking.

This ticket originally introduced mypy for static type checking. The project
has since switched from mypy to ty (ticket 98). Type-checking behavior is
now covered by test_98_template_python_project.py, which verifies that ty is
used and exercises the type-checker rules.

This file remains as a placeholder so that ticket 85 still has an associated
feature test file for the CI/CD pipeline.
"""

import pytest
from test_utils.command_runner import FeatureTestCommandContext


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_85_placeholder_type_checking_ticket(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """Placeholder test for ticket 85; type checking is now tested in test_98."""
    assert default_command_context.mock_project_root is not None
