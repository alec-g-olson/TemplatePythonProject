"""Tests for the calculator domain engine."""

import pytest
from template_python_project.calculators.calculator import calculate
from template_python_project.calculators.data_models import (
    CalculationRequest,
    CalculationResult,
    CalculationType,
)

_calculate_test_cases = [
    (
        CalculationRequest(operation=CalculationType.ADD, value1=2, value2=1),
        CalculationResult(result=3),
    ),
    (
        CalculationRequest(operation=CalculationType.SUBTRACT, value1=1, value2=2),
        CalculationResult(result=-1),
    ),
    (
        CalculationRequest(operation=CalculationType.MULTIPLY, value1=3, value2=3),
        CalculationResult(result=9),
    ),
    (
        CalculationRequest(operation=CalculationType.DIVIDE, value1=5, value2=2),
        CalculationResult(result=2.5),
    ),
]


@pytest.mark.parametrize(("request", "expected"), _calculate_test_cases)
def test_calculate_produces_correct_result(
    request: CalculationRequest, expected: CalculationResult
) -> None:
    """Each operation type produces the expected arithmetic result."""
    assert calculate(request) == expected


def test_calculate_covers_all_operation_types() -> None:
    """Test cases cover every member of CalculationType."""
    tested_types = {case[0].operation for case in _calculate_test_cases}
    assert tested_types == set(CalculationType)


def test_calculate_divide_by_zero_raises() -> None:
    """Division by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError):
        calculate(
            CalculationRequest(
                operation=CalculationType.DIVIDE, value1=199, value2=0
            )
        )
