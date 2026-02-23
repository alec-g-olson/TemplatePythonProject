"""Unit tests for build_logging."""

import logging

from build_support.build_logging import TRACE, register_trace_level

# Standard numeric level for TRACE (below logging.DEBUG).
_TRACE_LEVEL_VALUE = 5


def test_trace_level_value() -> None:
    """TRACE is below DEBUG (10) so it can be used for verbose task output."""
    assert TRACE == _TRACE_LEVEL_VALUE
    assert TRACE < logging.DEBUG


def test_register_trace_level() -> None:
    """register_trace_level makes LOG_LEVEL=TRACE and getLevelName work."""
    register_trace_level()
    assert logging.getLevelName(TRACE) == "TRACE"
