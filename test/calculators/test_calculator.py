import math

import pytest

from template_python_project.calculators.calculator import calculate_result
from template_python_project.calculators.dataclasses import (
    CalculationType,
    CalculatorInput,
    CalculatorOutput,
)


@pytest.mark.parametrize(
    "input_vals, result",
    [
        (
            CalculatorInput(typeOfCalc=CalculationType.ADD, value1=2, value2=1),
            CalculatorOutput(result=3),
        ),
        (
            CalculatorInput(typeOfCalc=CalculationType.SUBTRACT, value1=1, value2=2),
            CalculatorOutput(result=-1),
        ),
        (
            CalculatorInput(typeOfCalc=CalculationType.MULTIPLY, value1=3, value2=3),
            CalculatorOutput(result=9),
        ),
        (
            CalculatorInput(typeOfCalc=CalculationType.DIVIDE, value1=5, value2=2),
            CalculatorOutput(result=2.5),
        ),
        (
            CalculatorInput(typeOfCalc="invalid", value1=5, value2=2),
            CalculatorOutput(result=float("Nan")),
        ),
    ],
)
def test_calculate_result(input_vals, result):
    if math.isnan(result.result):
        assert math.isnan(calculate_result(input_vals).result)
    else:
        assert calculate_result(input_vals) == result


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculate_result(
            CalculatorInput(typeOfCalc=CalculationType.DIVIDE, value1=199, value2=0)
        )
