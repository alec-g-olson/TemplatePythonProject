"""Unit tests for versioned_model.pydantic_semver_annotation."""

import pytest
from pydantic import BaseModel, ValidationError
from semver import Version
from template_python_project.api.versioned_model.pydantic_semver_annotation import (
    PydanticSemVer,
)


class _SemVerModel(BaseModel):
    """Minimal model using PydanticSemVer for a version field."""

    version: PydanticSemVer


@pytest.mark.parametrize("input_value", [Version.parse("1.2.3"), "1.2.3"])
def test_pydantic_semver_accepts_version_and_string(input_value: object) -> None:
    """PydanticSemVer accepts both Version instances and strings."""
    model = _SemVerModel(version=input_value)
    assert isinstance(model.version, Version)
    assert model.version == Version.parse("1.2.3")


def test_pydantic_semver_serializes_version_as_string() -> None:
    """PydanticSemVer serializes the version field to a string."""
    model = _SemVerModel(version="2.0.0")
    dumped = model.model_dump()
    assert dumped["version"] == "2.0.0"

    json_str = model.model_dump_json()
    assert '"version":"2.0.0"' in json_str


def test_pydantic_semver_rejects_invalid_string() -> None:
    """Invalid semantic version strings raise a Pydantic validation error."""
    with pytest.raises(ValidationError) as exc_info:
        _SemVerModel(version="not-a-version")

    message = str(exc_info.value)
    assert "not a valid semantic version string" in message


def test_pydantic_semver_json_schema_has_semver_metadata() -> None:
    """JSON schema for PydanticSemVer includes semver-specific metadata."""
    schema = _SemVerModel.model_json_schema()
    version_schema = schema["properties"]["version"]

    assert version_schema["type"] == "string"
    assert version_schema["format"] == "semver"
    assert "Semantic version" in version_schema["description"]
    assert version_schema["examples"] == ["1.0.0", "2.1.3"]
