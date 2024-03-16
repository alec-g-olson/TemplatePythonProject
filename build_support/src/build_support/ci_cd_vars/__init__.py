"""Contains logic for all tasks that calculates variable used by tasks.

The functions, constants, and enums in these files are held here so that they can be
imported to tasks in ci_cd_tasks without fear of circular dependencies.

Modules:
    | file_and_dir_path_vars: All path variables and enforcement of project
        structure should go here.
    | git_status_vars: Holds functions that reflect the current git status.
    | machine_introspection_vars: Reports information about the machine the build is
        running on.
    | project_setting_vars: Reports project setting information.  Usually by parsing
        config files.
    | docker_vars: Variables and functions that relate to making docker calls.
    | python_vars: Variables that are only useful in the context of python
        building and testing.
    | project_structure: Variables and functions that relate to the top level structure
        of this project.
    | subproject_structure: Variables and functions that relate to the structure of
        subprojects of this project.
"""
