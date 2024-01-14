import pytest

from template_python_project.calculators.calculator import calculate_result
from template_python_project.calculators.dataclasses import (
    CalculationType,
    CalculatorInput,
    CalculatorOutput,
)

calculate_results_test_cases = [
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
]


@pytest.mark.parametrize("input_values, result", calculate_results_test_cases)
def test_calculate_result(input_values, result):
    assert calculate_result(input_values) == result


def test_calculate_result_all_types_covered():
    assert len(
        {input_value[0].typeOfCalc for input_value in calculate_results_test_cases}
    ) == len(CalculationType)


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculate_result(
            CalculatorInput(typeOfCalc=CalculationType.DIVIDE, value1=199, value2=0)
        )
