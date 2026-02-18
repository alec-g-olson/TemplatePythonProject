"""Tests for versioned API data models: CalculatorInput and CalculatorOutput."""

from typing import Any

import pytest
from pydantic import ValidationError
from semver import Version
from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.data_models import CalculationType


# ---------------------------------------------------------------------------
# CalculatorInput — construction and validation
# ---------------------------------------------------------------------------


@pytest.fixture()
def calculator_input_dict() -> dict[str, Any]:
    """Valid raw dict for constructing a CalculatorInput."""
    return {"type_of_calc": "ADD", "value1": 5.1, "value2": 10.0}


@pytest.fixture()
def calculator_input_obj() -> CalculatorInput:
    """A CalculatorInput constructed from known-good values."""
    return CalculatorInput(
        type_of_calc=CalculationType.ADD, value1=5.1, value2=10.0
    )


def test_calculator_input_defaults_to_current_version(
    calculator_input_obj: CalculatorInput,
) -> None:
    """When data_model_version is omitted, it defaults to current_version."""
    assert calculator_input_obj.data_model_version == Version(
        major=1, minor=0, patch=0
    )


def test_calculator_input_validates_from_dict(
    calculator_input_dict: dict[str, Any], calculator_input_obj: CalculatorInput
) -> None:
    """A valid dict round-trips through model_validate to the expected object."""
    assert CalculatorInput.model_validate(calculator_input_dict) == calculator_input_obj


def test_calculator_input_rejects_invalid_type(
    calculator_input_dict: dict[str, Any],
) -> None:
    """An invalid type_of_calc value is rejected."""
    calculator_input_dict["type_of_calc"] = "INVALID"
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_calculator_input_rejects_non_numeric_value1(
    calculator_input_dict: dict[str, Any],
) -> None:
    """A non-numeric value1 is rejected."""
    calculator_input_dict["value1"] = "four"
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_calculator_input_rejects_non_numeric_value2(
    calculator_input_dict: dict[str, Any],
) -> None:
    """A non-numeric value2 is rejected."""
    calculator_input_dict["value2"] = "four"
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_calculator_input_rejects_extra_fields() -> None:
    """Extra fields are forbidden by VersionedModel's strict config."""
    with pytest.raises(ValidationError):
        CalculatorInput(
            type_of_calc=CalculationType.ADD,
            value1=1.0,
            value2=2.0,
            extra_field="bad",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# CalculatorInput — serialization round-trips
# ---------------------------------------------------------------------------


def test_calculator_input_dump_round_trips(
    calculator_input_obj: CalculatorInput,
) -> None:
    """model_dump produces a dict that model_validate restores to an equal object."""
    dumped = calculator_input_obj.model_dump()
    restored = CalculatorInput.model_validate(dumped)
    assert restored == calculator_input_obj


def test_calculator_input_json_round_trips(
    calculator_input_obj: CalculatorInput,
) -> None:
    """model_dump_json produces JSON that model_validate_json restores."""
    json_str = calculator_input_obj.model_dump_json()
    restored = CalculatorInput.model_validate_json(json_str)
    assert restored == calculator_input_obj


# ---------------------------------------------------------------------------
# CalculatorOutput — construction and validation
# ---------------------------------------------------------------------------


@pytest.fixture()
def calculator_output_dict() -> dict[str, Any]:
    """Valid raw dict for constructing a CalculatorOutput."""
    return {"result": 5.1}


@pytest.fixture()
def calculator_output_obj() -> CalculatorOutput:
    """A CalculatorOutput constructed from a known-good value."""
    return CalculatorOutput(result=5.1)


def test_calculator_output_defaults_to_current_version(
    calculator_output_obj: CalculatorOutput,
) -> None:
    """When data_model_version is omitted, it defaults to current_version."""
    assert calculator_output_obj.data_model_version == Version(
        major=1, minor=0, patch=0
    )


def test_calculator_output_validates_from_dict(
    calculator_output_dict: dict[str, Any], calculator_output_obj: CalculatorOutput
) -> None:
    """A valid dict round-trips through model_validate to the expected object."""
    assert (
        CalculatorOutput.model_validate(calculator_output_dict) == calculator_output_obj
    )


def test_calculator_output_rejects_non_numeric_result(
    calculator_output_dict: dict[str, Any],
) -> None:
    """A non-numeric result is rejected."""
    calculator_output_dict["result"] = "ten"
    with pytest.raises(ValidationError):
        CalculatorOutput.model_validate(calculator_output_dict)


# ---------------------------------------------------------------------------
# CalculatorOutput — serialization round-trips
# ---------------------------------------------------------------------------


def test_calculator_output_dump_round_trips(
    calculator_output_obj: CalculatorOutput,
) -> None:
    """model_dump produces a dict that model_validate restores to an equal object."""
    dumped = calculator_output_obj.model_dump()
    restored = CalculatorOutput.model_validate(dumped)
    assert restored == calculator_output_obj


def test_calculator_output_json_round_trips(
    calculator_output_obj: CalculatorOutput,
) -> None:
    """model_dump_json produces JSON that model_validate_json restores."""
    json_str = calculator_output_obj.model_dump_json()
    restored = CalculatorOutput.model_validate_json(json_str)
    assert restored == calculator_output_obj
