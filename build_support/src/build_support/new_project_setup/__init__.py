"""Contains the logic for the creation of new projects from this template.

There are many files that have to change in order for a new project to be created
successfully.  However, the values needed to make the new project should all be
available in the new_project_settings.yaml, and the work should all be managed by
MakeProjectFromTemplate task in the setup_new_project module.

Modules:
    | new_project_data_models.py: Contains the data models that can parse
        new_project_settings.yaml. Once parsed it is available in code.
    | license_templates.py: Contains the basic license template information.  Split
        out from setup_license so that setup_new_project didn't create a circular
        dependency.
    | setup_license.py: Contains the logic for setting up a new license based on the
        values in new_project_settings.yaml.
    | update_pyproject_toml.py: Contains the logic for updating pyproject.toml based on
        the new_project_settings.yaml.
    | update_folder_names.py: Contains the logic for updating file and folder names
        based on the new_project_settings.yaml.
    | setup_new_project.py: Contains the MakeProjectFromTemplate Task.
"""
