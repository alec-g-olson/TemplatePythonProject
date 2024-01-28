import pytest
import yaml
from new_project_setup.new_project_dataclass import ProjectSettings

data_dict = {
    "name": "test_project_name",
    "license": "gpl-3.0",
    "organization": "Someone Nice",
}


@pytest.fixture
def project_yaml_str() -> str:
    return yaml.dump(data_dict)


def test_load(project_yaml_str: str):
    project_setting = ProjectSettings.from_yaml(project_yaml_str)
    assert project_setting == ProjectSettings(**data_dict)


def test_dump(project_yaml_str: str):
    project_setting = ProjectSettings(**data_dict)
    assert project_setting.to_yaml() == project_yaml_str
