"""Tests for VersionedModel — version validation, serialization, and migration."""

from typing import Any, ClassVar, override

import pytest
from template_python_project.versioned_model.versioned_model import VersionedModel
from pydantic import ValidationError
from semver import Version

# ---------------------------------------------------------------------------
# Constants for ChildModelB coercion defaults
# ---------------------------------------------------------------------------

_NEW_VALUE_1_DEFAULT: int = 100
_NEW_VALUE_2_DEFAULT: float = 200.0


# ---------------------------------------------------------------------------
# Test model classes
# ---------------------------------------------------------------------------


class SimpleVersionedModel(VersionedModel):
    """Minimal versioned model."""

    current_version: ClassVar[Version] = Version(major=50, minor=25, patch=3)
    lowest_supported_version: ClassVar[Version] = Version(major=25, minor=0, patch=0)

    name: str


class ChildModelA(SimpleVersionedModel):
    """Child model with lower version numbers than it's parent."""

    current_version = Version(major=2, minor=1, patch=0)
    lowest_supported_version = Version(major=2, minor=1, patch=0)


class ChildModelB(SimpleVersionedModel):
    """Versioned model with more fields than its parent.

    Migration history:
      - 5.0.0: original schema (no new_value_1, no new_value_2)
      - 5.1.0: added new_value_1
      - 5.2.0: added new_value_2 (current)
    """

    current_version = Version(major=5, minor=2, patch=0)
    lowest_supported_version = Version(major=5, minor=0, patch=0)

    new_value_1: int
    new_value_2: float

    @classmethod
    @override
    def _coerce_to_most_recent_version(cls, data: Any) -> Any:  # type: ignore[override]
        """Backfill new_value_1 and new_value_2 for payloads from older versions."""
        version = cls._get_valid_version_if_any_from_raw_data(data=data)
        if (
            version is not None
            and version < cls.current_version
            and isinstance(data, dict)
        ):
            if version <= Version(major=5, minor=0, patch=0):
                data["new_value_1"] = _NEW_VALUE_1_DEFAULT
            if version <= Version(major=5, minor=1, patch=0):  # pragma: no cov - style
                data["new_value_2"] = _NEW_VALUE_2_DEFAULT
            data["data_model_version"] = str(cls.current_version)
        return data


# ---------------------------------------------------------------------------
# TestBasicVersionedModel — basic construction and version validation
# ---------------------------------------------------------------------------


def test_simple_versioned_model_defaults_to_current_version() -> None:
    """When data_model_version is omitted, it defaults to current_version."""
    model = SimpleVersionedModel(name="example")
    assert model.data_model_version == Version(major=50, minor=25, patch=3)


@pytest.mark.parametrize(
    "data_model_version", [Version(major=50, minor=10, patch=0), "50.10.0"]
)
def test_simple_versioned_model_accepts_versions_within_supported_range(
    data_model_version: Any,
) -> None:
    """SimpleVersionedModel accepts versions within [lowest_supported, current]."""
    model = SimpleVersionedModel(name="ok", data_model_version=data_model_version)
    assert model.data_model_version == Version(major=50, minor=10, patch=0)


@pytest.mark.parametrize(
    "bad_version",
    [
        "10.0.0",  # below lowest_supported_version
        "99.0.0",  # above current_version
    ],
)
def test_simple_versioned_model_rejects_versions_outside_supported_range(
    bad_version: str,
) -> None:
    """SimpleVersionedModel rejects versions lower than lowest or greater than current."""
    with pytest.raises(ValidationError) as exc_info:
        SimpleVersionedModel(name="bad", data_model_version=bad_version)
    msg = str(exc_info.value)
    assert "Model undefined for versions" in msg


# ---------------------------------------------------------------------------
# TestSerializationViaModelDump — model_dump / model_validate round-trips
# ---------------------------------------------------------------------------


def test_model_dump_uses_json_mode_and_serializes_version() -> None:
    """model_dump defaults to JSON mode and serializes Version fields as strings."""
    model = SimpleVersionedModel(name="dump-test")
    dumped = model.model_dump()
    assert dumped["name"] == "dump-test"
    # data_model_version should be serialized as a string due to PydanticSemVer
    assert isinstance(dumped["data_model_version"], str)
    # Round-trip through validation
    restored = SimpleVersionedModel.model_validate(dumped)
    assert restored == model


# ---------------------------------------------------------------------------
# TestSerializationViaModelDumpJson — model_dump_json / model_validate_json
# ---------------------------------------------------------------------------


def test_model_dump_json_serializes_to_string_and_round_trips() -> None:
    """model_dump_json uses serialize_as_any=True and supports round trip."""
    model = SimpleVersionedModel(name="json-test")
    json_str = model.model_dump_json()
    # Expect a JSON object with data_model_version rendered as a string
    assert '"data_model_version":"' in json_str
    restored = SimpleVersionedModel.model_validate_json(json_str)
    assert restored == model


# ---------------------------------------------------------------------------
# TestChildModelA — pinned single-version model (lowest == current == 2.1.0)
# ---------------------------------------------------------------------------


def test_child_model_a_pins_single_supported_version() -> None:
    """ChildModelA only accepts its pinned version (2.1.0)."""
    model = ChildModelA(name="child-a")
    assert model.data_model_version == Version(major=2, minor=1, patch=0)

    # Explicit same version is accepted
    explicit = ChildModelA(name="child-a", data_model_version="2.1.0")
    assert explicit.data_model_version == Version(major=2, minor=1, patch=0)

    # Lower and higher versions are rejected
    for bad in ["2.0.9", "3.0.0"]:
        with pytest.raises(ValidationError):
            ChildModelA(name="bad", data_model_version=bad)


# ---------------------------------------------------------------------------
# TestChildModelBBasic — basic construction and serialization
# ---------------------------------------------------------------------------


def test_child_model_b_basic_construction_and_dump() -> None:
    """ChildModelB constructs with current version and serializes correctly."""
    model = ChildModelB(name="child-b", new_value_1=1, new_value_2=2.0)
    assert model.data_model_version == Version(major=5, minor=2, patch=0)

    dumped = model.model_dump()
    assert dumped["name"] == "child-b"
    assert dumped["new_value_1"] == 1
    assert dumped["new_value_2"] == 2.0
    assert dumped["data_model_version"] == "5.2.0"


# ---------------------------------------------------------------------------
# TestChildModelBCoercion — version coercion / migration
# ---------------------------------------------------------------------------


def test_child_model_b_coerces_5_1_0_payload_to_current_version() -> None:
    """Payloads from version 5.1.0 get new_value_2 backfilled and version bumped."""
    raw = {"name": "from-5.1.0", "new_value_1": 10, "data_model_version": "5.1.0"}
    model = ChildModelB.model_validate(raw)
    assert model.data_model_version == Version(major=5, minor=2, patch=0)
    # new_value_1 preserved, new_value_2 backfilled
    assert model.new_value_1 == 10
    assert model.new_value_2 == _NEW_VALUE_2_DEFAULT


def test_child_model_b_coerces_5_0_0_payload_to_current_version() -> None:
    """Payloads from version 5.0.0 get both new values backfilled and version bumped."""
    raw = {"name": "from-5.0.0", "data_model_version": "5.0.0"}
    model = ChildModelB.model_validate(raw)
    assert model.data_model_version == Version(major=5, minor=2, patch=0)
    assert model.new_value_1 == _NEW_VALUE_1_DEFAULT
    assert model.new_value_2 == _NEW_VALUE_2_DEFAULT


def test_child_model_b_rejects_versions_outside_supported_range() -> None:
    """ChildModelB rejects payloads with versions outside [5.0.0, 5.2.0]."""
    for bad in ["4.9.9", "6.0.0"]:
        raw = {"name": "bad", "data_model_version": bad}
        with pytest.raises(ValidationError):
            ChildModelB.model_validate(raw)
