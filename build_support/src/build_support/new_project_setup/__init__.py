"""The package was created to organize the creation of new projects from this template.

There are many files that have to change in order for a new project to be created
successfully.  However, the values needed to make the new project should all be
available in the project_settings.yaml, and the work should all be managed by
MakeProjectFromTemplate task in the setup_new_project module.

new_project_data_models.py: Contains the data models that can parse project_settings.yaml.
Once parsed it is available in code.
setup_license.py: Contains the logic for setting up a new license based on the values
in project_settings.yaml.
update_pyproject_toml.py: Contains the logic for updating pyproject.toml based on the
project_settings.yaml.
setup_new_project.py: Contains the MakeProjectFromTemplate Task.
"""
