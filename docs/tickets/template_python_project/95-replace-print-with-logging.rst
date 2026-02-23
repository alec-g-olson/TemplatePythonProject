Replace Print Statements with Configurable Logging Levels
=========================================================

Overview
--------
Replace direct ``print()`` usage in the build pipeline with a standard logging
facility and configurable log level. This lets developers and agents choose how
much output they see when running ``make`` (e.g. quiet workflow-only vs. full
command and task output), reducing noise while keeping important progress and
failure information visible.

Requirements
------------

User Flow
~~~~~~~~~
1. User runs any ``make`` target (e.g. ``make test``, ``make format``).
2. Build runs inside the build container; amount of console output depends on
   the configured log level (e.g. via environment variable or Make variable).
3. At the most verbose level, behavior matches current output (workflow lines,
   commands, and full task stdout/stderr). At quieter levels, only higher-level
   workflow messages (and failures) are shown.

Output Tiers and Suggested Log Levels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Map existing output to logging levels so that a single level controls what is
printed. Suggested mapping:

**Highest level — workflow only (e.g. default or INFO):**

- "Will execute the following tasks:"
- Bullet list of task names
- "Starting: <TaskName>" per task
- Build run report (YAML summary of task durations)

**Mid level — commands (e.g. DEBUG):**

- The exact command line for each subprocess (e.g. ``docker run ... python ...``)
  as currently printed by ``process_runner`` before running.

**Highest verbosity — task output (e.g. DEBUG or a dedicated verbose level):**

- Full stdout/stderr of each task (e.g. pytest output, coverage report, linter
  output) as currently streamed by ``process_runner.resolve_process_results``.

**Always shown (independent of level):**

- Failures: non-zero exit codes and the command that failed (already partially
  handled when ``ProcessVerbosity.SILENT`` and failure).
- Unhandled exceptions in the build entrypoint (e.g. in ``execute_build_steps``)
  should be logged at ERROR and/or re-raised so they are visible.

Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~
- Introduce a single, consistent way to set log level for the build (e.g.
  ``LOG_LEVEL`` or ``BUILD_LOG_LEVEL``) that is respected by all build_support
  code that currently uses ``print()``. Prefer standard library ``logging``.
- Replace all relevant ``print()`` calls in the build pipeline with appropriate
  log level calls. Key locations:
  - ``build_support/dag_engine.py``: workflow messages and run report (INFO or
    equivalent for default visibility).
  - ``build_support/process_runner.py``: command line (DEBUG), subprocess
    stdout/stderr (DEBUG or verbose), and failure message on non-zero exit
    (ERROR or always-visible).
  - ``build_support/execute_build_steps.py``: exception handler should use
    logging (ERROR) instead of ``print(e)``.
  - ``build_support/report_build_var.py``: output is the primary result of the
    script (docker command string). Either keep as the script’s intended stdout
    result (not “logging”) or document that it is emitted at a specific level
    when called from the build.
- Default log level should give a quiet-but-useful experience (e.g. workflow
  only), with an option to increase verbosity (e.g. ``make test
  LOG_LEVEL=DEBUG`` or equivalent) for debugging.
- Existing ``ProcessVerbosity`` (SILENT vs ALL) may be refactored or replaced
  by the new log-level behavior so that “silent” corresponds to minimal logging
  and “all” to maximum verbosity.

Acceptance Criteria / Feature Tests
-----------------------------------
- A feature test (or equivalent) verifies that when the build runs with the
  default log level, only workflow-level messages appear (task list, “Starting:
  …”, run report); no raw command lines and no full task output (e.g. no pytest
  session log) in the captured stdout/stderr.
- A feature test verifies that when the build runs with a verbose/debug log
  level, command lines are present in the output.
- A feature test verifies that when the build runs with maximum verbosity, full
  task output (e.g. pytest output) is present in the output.
- A feature test verifies that on task failure (non-zero exit), the failure
  and the failing command (or equivalent) are visible even at the quietest
  level.
- Unit tests for build_support modules that emit output are updated to assert
  on logging calls or log-level behavior where appropriate; 100% coverage is
  maintained.

Notes
-----
- Current ``print()`` locations: ``dag_engine.py`` (workflow + report),
  ``process_runner.py`` (command, stdout, stderr, failure message),
  ``execute_build_steps.py`` (exception), ``report_build_var.py`` (docker
  command string). Decide whether ``report_build_var`` output is “data” (stdout
  for consumption) vs “logging” and document.
- Consider documenting the chosen env/Make variable (e.g. ``LOG_LEVEL``) in
  ``docs/developer_tooling.rst`` or similar so developers and agents know how
  to reduce or increase build output.
