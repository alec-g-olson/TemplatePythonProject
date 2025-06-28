from typing import Any, cast

import pytest
from _pytest.fixtures import SubRequest
from pydantic import ValidationError
from template_python_project.calculators.data_models import (
    CalculationType,
    CalculatorInput,
    CalculatorOutput,
)


@pytest.fixture(params=list(CalculationType))
def calculation_type(request: SubRequest) -> CalculationType:
    return cast(CalculationType, request.param)


def test_calculation_type_to_str(calculation_type: CalculationType) -> None:
    assert str(calculation_type) == calculation_type.name


@pytest.fixture
def calculator_input_dict() -> dict[Any, Any]:
    return {"type_of_calc": CalculationType.ADD, "value1": 5.1, "value2": 10}


@pytest.fixture
def calculator_input_obj() -> CalculatorInput:
    return CalculatorInput(type_of_calc=CalculationType.ADD, value1=5.1, value2=10.0)


def test_load_calculator_input(
    calculator_input_dict: dict[Any, Any], calculator_input_obj: CalculatorInput
) -> None:
    assert CalculatorInput.model_validate(calculator_input_dict) == calculator_input_obj


def test_load_calculator_input_bad_type(calculator_input_dict: dict[Any, Any]) -> None:
    calculator_input_dict["type_of_calc"] = 4
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_load_calculator_input_bad_value1(
    calculator_input_dict: dict[Any, Any],
) -> None:
    calculator_input_dict["value1"] = "four"
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_load_calculator_input_bad_value2(
    calculator_input_dict: dict[Any, Any],
) -> None:
    calculator_input_dict["value2"] = "four"
    with pytest.raises(ValidationError):
        CalculatorInput.model_validate(calculator_input_dict)


def test_dump_calculator_input(
    calculator_input_dict: dict[Any, Any], calculator_input_obj: CalculatorInput
) -> None:
    assert calculator_input_obj.model_dump() == calculator_input_dict


@pytest.fixture
def calculator_output_dict() -> dict[Any, Any]:
    return {"result": 5.1}


@pytest.fixture
def calculator_output_obj() -> CalculatorOutput:
    return CalculatorOutput(result=5.1)


def test_load_calculator_output(
    calculator_output_dict: dict[Any, Any], calculator_output_obj: CalculatorOutput
) -> None:
    assert (
        CalculatorOutput.model_validate(calculator_output_dict) == calculator_output_obj
    )


def test_load_calculator_output_bad_type(
    calculator_output_dict: dict[Any, Any],
) -> None:
    calculator_output_dict["result"] = "ten"
    with pytest.raises(ValidationError):
        CalculatorOutput.model_validate(calculator_output_dict)


def test_dump_calculator_output(
    calculator_output_dict: dict[Any, Any], calculator_output_obj: CalculatorOutput
) -> None:
    assert calculator_output_obj.model_dump() == calculator_output_dict
