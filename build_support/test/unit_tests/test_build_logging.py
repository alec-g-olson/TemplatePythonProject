"""Unit tests for build_logging."""

import logging
from unittest.mock import patch

from build_support.build_logging import (
    TRACE,
    _configure_build_logging,
    register_trace_level,
)

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


def test_configure_build_logging_accepts_trace() -> None:
    """_configure_build_logging sets root level to TRACE when LOG_LEVEL=TRACE."""
    with patch.dict("os.environ", {"LOG_LEVEL": "TRACE"}, clear=False):
        _configure_build_logging()
    assert logging.root.level == TRACE


def test_configure_build_logging_invalid_level_falls_back_to_info() -> None:
    """_configure_build_logging falls back to INFO for invalid LOG_LEVEL."""
    with patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}, clear=False):
        _configure_build_logging()
    assert logging.root.level == logging.INFO


def test_configure_build_logging_accepts_standard_level() -> None:
    """_configure_build_logging uses standard level when LOG_LEVEL is DEBUG."""
    with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}, clear=False):
        _configure_build_logging()
    assert logging.root.level == logging.DEBUG
