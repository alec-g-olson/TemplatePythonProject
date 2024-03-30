from copy import copy

import pytest
import yaml
from pydantic import ValidationError

from build_support.new_project_setup.new_project_data_models import ProjectSettings

project_settings_data_dict = {
    "name": "test_project_name",
    "license": "gpl-3.0",
    "organization": {"name": "Someone Nice", "contact_email": "someone@nice.com"},
}


@pytest.fixture()
def project_yaml_str() -> str:
    return yaml.dump(project_settings_data_dict)


def test_load(project_yaml_str: str) -> None:
    project_setting = ProjectSettings.from_yaml(yaml_str=project_yaml_str)
    assert project_setting == ProjectSettings.model_validate(project_settings_data_dict)


def test_load_bad_name() -> None:
    bad_dict = copy(project_settings_data_dict)
    bad_dict["name"] = 4  # type: ignore[assignment]
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_bad_license() -> None:
    bad_dict = copy(project_settings_data_dict)
    bad_dict["license"] = 4  # type: ignore[assignment]
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_invalid_license() -> None:
    bad_dict = copy(project_settings_data_dict)
    bad_dict["license"] = "INVALID_LICENSE"
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_bad_organization() -> None:
    bad_dict = copy(project_settings_data_dict)
    bad_dict["organization"] = 4  # type: ignore[assignment]
    project_yaml_str = yaml.dump(bad_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_dump(project_yaml_str: str) -> None:
    project_setting = ProjectSettings.model_validate(project_settings_data_dict)
    assert project_setting.to_yaml() == project_yaml_str


def test_org_formatted_name_and_email() -> None:
    project_setting = ProjectSettings.model_validate(project_settings_data_dict)
    org = project_setting.organization
    assert org.formatted_name_and_email() == "Someone Nice <someone@nice.com>"
