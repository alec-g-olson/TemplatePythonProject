"""Domain engine for calculation operations.

This module implements pure business logic for basic arithmetic operations.
All functions accept only domain types (dataclasses and primitives) and
communicate via dataclasses.

Functions:
    calculate: Execute an arithmetic operation and return the result.
"""

from template_python_project.calculators.data_models import (
    CalculationType,
    CalculationRequest,
    CalculationResult,
)


def calculate(request: CalculationRequest) -> CalculationResult:
    """Perform arithmetic calculation based on the request.

    Args:
        request (CalculationRequest): The calculation parameters including operation
            type and two operands.

    Returns:
        CalculationResult: The result of the calculation.

    Raises:
        ZeroDivisionError: If division by zero is attempted.
    """
    if request.operation == CalculationType.ADD:
        result = request.value1 + request.value2
    elif request.operation == CalculationType.SUBTRACT:
        result = request.value1 - request.value2
    elif request.operation == CalculationType.MULTIPLY:
        result = request.value1 * request.value2
    else:  # DIVIDE
        result = request.value1 / request.value2
    return CalculationResult(result=result)
