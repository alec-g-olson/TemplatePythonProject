"""Package for managing build plans.

- dag_engine.py has the basic logic for running Tasks.
- execute_build_steps.py is a "main" that runs tasks.
- report_build_var.py is a "main" that reports variables.
- build_tasks is where most tasks should be implemented.
- new_project_setup holds the logic for the MakeProjectFromTemplate task.
    It is a particularly complex task that is conceptually different from
    the other build tasks.
- build_vars is where build variables can be calculated.
"""
