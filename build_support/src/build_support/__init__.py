"""Package for managing build plans.

SubPackages:
    | ci_cd_tasks: All tasks that are part of the standard build pipeline should be
        implemented within this package.
    | ci_cd_vars: All variables used in the standard build pipeline should be
        calculated within this package.  This is done to prevent circular dependencies.
    | new_project_setup: This package contains the logic needed for setting up a new
        project that is not part of the standard pipeline.

Modules:
    | dag_engine.py: Contains the logic for resolving task dependencies and running
        tasks in a coherent order.
    | execute_build_steps.py: A "main" that runs tasks.
    | report_build_var.py: A "main" that reports variables.
"""
