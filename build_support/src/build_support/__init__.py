"""Package for managing build plans.

SubPackages:
    | ci_cd_tasks: All tasks that are part of the standard build pipeline should be
        implemented within this package.
    | ci_cd_vars: All variables used in the standard build pipeline should be
        calculated within this package.  This is done to prevent circular dependencies.
    | new_project_setup: This package contains the logic needed for setting up a new
        project that is not part of the standard pipeline.

Modules:
    | dag_engine: Contains the logic for resolving task dependencies and running
        tasks in a coherent order.
    | dump_ci_cd_run_info: A "main" that records project level variables for the CI/CD
        pipeline to a file for use during CI/CD.
    | execute_build_steps: A "main" that runs tasks.
    | file_caching: Logic for checking if a file has been modified since last execution.
    | process_runner: Contains the logic for executing subprocesses.
    | report_build_var: A "main" that reports variables.
"""
