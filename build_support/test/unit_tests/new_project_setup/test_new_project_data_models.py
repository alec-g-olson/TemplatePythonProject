import pytest
import yaml
from pydantic import ValidationError

from build_support.new_project_setup.new_project_data_models import ProjectSettings


@pytest.fixture()
def project_settings_data_dict() -> dict:
    return {
        "name": "test_project_name",
        "license": "gpl-3.0",
        "organization": {"name": "Someone Nice", "contact_email": "someone@nice.com"},
    }


@pytest.fixture()
def project_yaml_str(project_settings_data_dict: dict) -> str:
    return yaml.dump(project_settings_data_dict)


def test_load(project_yaml_str: str, project_settings_data_dict: dict) -> None:
    project_setting = ProjectSettings.from_yaml(yaml_str=project_yaml_str)
    assert project_setting == ProjectSettings.model_validate(project_settings_data_dict)


def test_load_bad_name(project_settings_data_dict: dict) -> None:
    project_settings_data_dict["name"] = 4
    project_yaml_str = yaml.dump(project_settings_data_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_bad_license(project_settings_data_dict: dict) -> None:
    project_settings_data_dict["license"] = 4
    project_yaml_str = yaml.dump(project_settings_data_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_invalid_license(project_settings_data_dict: dict) -> None:
    project_settings_data_dict["license"] = "INVALID_LICENSE"
    project_yaml_str = yaml.dump(project_settings_data_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_load_bad_organization(project_settings_data_dict: dict) -> None:
    project_settings_data_dict["organization"] = 4
    project_yaml_str = yaml.dump(project_settings_data_dict)
    with pytest.raises(ValidationError):
        ProjectSettings.from_yaml(yaml_str=project_yaml_str)


def test_dump(project_yaml_str: str, project_settings_data_dict: dict) -> None:
    project_setting = ProjectSettings.model_validate(project_settings_data_dict)
    assert project_setting.to_yaml() == project_yaml_str


def test_org_formatted_name_and_email(project_settings_data_dict: dict) -> None:
    project_setting = ProjectSettings.model_validate(project_settings_data_dict)
    org = project_setting.organization
    assert org.formatted_name_and_email() == "Someone Nice <someone@nice.com>"
