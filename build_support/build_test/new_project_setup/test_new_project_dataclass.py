from copy import copy

import pytest
import yaml
from new_project_setup.new_project_dataclass import ProjectSettings

project_settings_data_dict = {
    "name": "test_project_name",
    "license": "gpl-3.0",
    "organization": "Someone Nice",
}


@pytest.fixture
def project_yaml_str() -> str:
    return yaml.dump(project_settings_data_dict)


def test_load(project_yaml_str: str):
    project_setting = ProjectSettings.from_yaml(project_yaml_str)
    assert project_setting == ProjectSettings(**project_settings_data_dict)


def test_load_bad_name():
    bad_dict = copy(project_settings_data_dict)
    bad_dict["name"] = 4
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        ProjectSettings.from_yaml(project_yaml_str)


def test_load_bad_license():
    bad_dict = copy(project_settings_data_dict)
    bad_dict["license"] = 4
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        ProjectSettings.from_yaml(project_yaml_str)


def test_load_invalid_license():
    bad_dict = copy(project_settings_data_dict)
    bad_dict["license"] = "INVALID_LICENSE"
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        ProjectSettings.from_yaml(project_yaml_str)


def test_load_bad_organization():
    bad_dict = copy(project_settings_data_dict)
    bad_dict["organization"] = 4
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValueError):
        ProjectSettings.from_yaml(project_yaml_str)


def test_dump(project_yaml_str: str):
    project_setting = ProjectSettings(**project_settings_data_dict)
    assert project_setting.to_yaml() == project_yaml_str
