"""Tests for the calculator domain engine."""

from enum import StrEnum
from typing import cast

import pytest
from template_python_project.calculators.calculator import calculate
from template_python_project.calculators.data_models import (
    CalculationRequest,
    CalculationResult,
    CalculationType,
)


class _FakeCalculationType(StrEnum):
    """Test-only enum with an unimplemented member to trigger the default branch."""

    IMPLEMENTED = CalculationType.ADD.value
    UNIMPLEMENTED = "UNIMPLEMENTED"


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


@pytest.mark.parametrize(("calc_request", "expected"), _calculate_test_cases)
def test_calculate_produces_correct_result(
    calc_request: CalculationRequest, expected: CalculationResult
) -> None:
    """Each operation type produces the expected arithmetic result."""
    assert calculate(calc_request) == expected


def test_calculate_covers_all_operation_types() -> None:
    """Test cases cover every member of CalculationType."""
    tested_types = {case[0].operation for case in _calculate_test_cases}
    assert tested_types == set(CalculationType)


def test_calculate_divide_by_zero_raises() -> None:
    """Division by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError):
        calculate(
            CalculationRequest(operation=CalculationType.DIVIDE, value1=199, value2=0)
        )


def test_calculate_unimplemented_operation_raises() -> None:
    """Unimplemented operation type raises NotImplementedError (covers default case)."""
    request_with_unimplemented_op = cast(
        CalculationRequest,
        CalculationRequest(
            operation=_FakeCalculationType.UNIMPLEMENTED, value1=1.0, value2=2.0
        ),
    )
    with pytest.raises(NotImplementedError) as exc_info:
        calculate(request_with_unimplemented_op)
    assert "No implementation for operation" in str(exc_info.value)
    assert "UNIMPLEMENTED" in str(exc_info.value)
