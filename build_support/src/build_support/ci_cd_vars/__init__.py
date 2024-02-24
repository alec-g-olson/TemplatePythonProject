"""Contains logic for all tasks that calculates variable used by tasks.

The functions, constants, and enums in these files are held here so that they can be
imported to tasks in ci_cd_tasks without fear of circular dependencies.

Modules:
    | file_and_dir_path_vars.py: All path variables and enforcement of project
        structure should go here.
    | git_status_vars.py: Holds functions that reflect the current git status.
    | machine_introspection_vars.py: Reports information about the machine the build is
        running on.
    | project_setting_vars.py: Reports project setting information.  Usually by parsing
        config files.
    | docker_vars.py: Variables and functions that relate to making docker calls.
    | python_vars.py: Variables that are only useful in the context of python
        building and testing.
"""
