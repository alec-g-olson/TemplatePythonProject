"""Build pipeline logging: TRACE level and registration.

The build uses three verbosity levels: INFO (steps only), DEBUG (+ command
lines), TRACE (+ task stdout/stderr). TRACE is a custom level below DEBUG.
This module defines the TRACE constant and registers it with the standard
logging module so LOG_LEVEL=TRACE works.

Attributes:
    | TRACE: Numeric log level (5) for most verbose build output.
"""

import logging
import os
import sys

# Below DEBUG (10); used for task stdout/stderr so they can be suppressed at DEBUG.
TRACE = 5


def register_trace_level() -> None:
    """Register the TRACE level name with the logging module.

    Call once at build startup (e.g. from execute_build_steps) so that
    LOG_LEVEL=TRACE is recognized and logger.log(TRACE, ...) displays
    correctly.

    Returns:
        None
    """
    logging.addLevelName(TRACE, "TRACE")


def _configure_build_logging() -> None:
    """Configure build logging from LOG_LEVEL.

    Default is INFO (steps only). DEBUG adds commands. TRACE adds stdout/stderr.
    Invalid or unset values fall back to INFO.

    Returns:
        None
    """
    register_trace_level()
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = TRACE if level_name == "TRACE" else logging.INFO
    logging.basicConfig(
        level=level, format="%(message)s", stream=sys.stdout, force=True
    )
