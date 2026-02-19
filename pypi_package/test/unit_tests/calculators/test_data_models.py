"""Tests for domain data models.

Covers CalculationType, CalculationRequest, and CalculationResult.
"""

from typing import cast

import pytest
from _pytest.fixtures import SubRequest
from template_python_project.calculators.data_models import (
    CalculationRequest,
    CalculationResult,
    CalculationType,
)

_REQUEST_VALUE_1 = 3.5
_REQUEST_VALUE_2 = 7.0
_RESULT_VALUE = 42.0

# ---------------------------------------------------------------------------
# CalculationType
# ---------------------------------------------------------------------------


@pytest.fixture(params=list(CalculationType))
def calculation_type(request: SubRequest) -> CalculationType:
    """Yield each CalculationType member in turn."""
    return cast(CalculationType, request.param)


def test_calculation_type_str_returns_name(calculation_type: CalculationType) -> None:
    """str(member) returns the member's name, not its value."""
    assert str(calculation_type) == calculation_type.name


# ---------------------------------------------------------------------------
# CalculationRequest
# ---------------------------------------------------------------------------


def test_calculation_request_stores_fields() -> None:
    """CalculationRequest exposes the fields it was constructed with."""
    request = CalculationRequest(
        operation=CalculationType.ADD, value1=_REQUEST_VALUE_1, value2=_REQUEST_VALUE_2
    )
    assert request.operation == CalculationType.ADD
    assert request.value1 == _REQUEST_VALUE_1
    assert request.value2 == _REQUEST_VALUE_2


def test_calculation_request_is_frozen() -> None:
    """CalculationRequest is immutable after construction."""
    request = CalculationRequest(operation=CalculationType.ADD, value1=1.0, value2=2.0)
    with pytest.raises(AttributeError):
        request.value1 = 99.0  # type: ignore[misc]


def test_calculation_request_equality() -> None:
    """Two CalculationRequests with the same fields are equal."""
    request_a = CalculationRequest(
        operation=CalculationType.MULTIPLY, value1=2.0, value2=3.0
    )
    request_b = CalculationRequest(
        operation=CalculationType.MULTIPLY, value1=2.0, value2=3.0
    )
    assert request_a == request_b


# ---------------------------------------------------------------------------
# CalculationResult
# ---------------------------------------------------------------------------


def test_calculation_result_stores_result() -> None:
    """CalculationResult exposes the result it was constructed with."""
    result = CalculationResult(result=_RESULT_VALUE)
    assert result.result == _RESULT_VALUE


def test_calculation_result_is_frozen() -> None:
    """CalculationResult is immutable after construction."""
    result = CalculationResult(result=1.0)
    with pytest.raises(AttributeError):
        result.result = 99.0  # type: ignore[misc]


def test_calculation_result_equality() -> None:
    """Two CalculationResults with the same value are equal."""
    assert CalculationResult(result=5.5) == CalculationResult(result=5.5)
