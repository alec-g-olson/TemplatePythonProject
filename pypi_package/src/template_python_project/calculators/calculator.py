"""Domain engine for calculation operations.

This module implements pure business logic for basic arithmetic operations.
All functions accept only domain types (dataclasses and primitives) and
communicate via dataclasses.

Functions:
    calculate: Execute an arithmetic operation and return the result.
"""

from template_python_project.calculators.data_models import (
    CalculationRequest,
    CalculationResult,
    CalculationType,
)


def calculate(request: CalculationRequest) -> CalculationResult:
    """Perform arithmetic calculation based on the request.

    Args:
        request (CalculationRequest): The calculation parameters including operation
            type and two operands.

    Returns:
        CalculationResult: The result of the calculation.

    Raises:
        NotImplementedError: If the operation type has no implementation.
        ZeroDivisionError: If division by zero is attempted.
    """
    match request.operation:
        case CalculationType.ADD:
            result = request.value1 + request.value2
        case CalculationType.SUBTRACT:
            result = request.value1 - request.value2
        case CalculationType.MULTIPLY:
            result = request.value1 * request.value2
        case CalculationType.DIVIDE:
            result = request.value1 / request.value2
        case _:
            msg = f"No implementation for operation {request.operation!r}"
            raise NotImplementedError(msg)
    return CalculationResult(result=result)
