"""Service functions for calculator API.

This module provides the public service function that translates from versioned
API models to internal domain types, calls the domain engine, and wraps results
in versioned output models.

Functions:
    calculate: The public service function for calculations.
"""

from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.calculator import calculate as calculate_domain
from template_python_project.calculators.data_models import CalculationRequest


def calculate(request: CalculatorInput) -> CalculatorOutput:
    """Execute calculation via the public API.

    Translates from versioned input model to domain types, calls the domain
    engine, and wraps the result in a versioned output model.

    Args:
        request (CalculatorInput): The versioned request with calculation parameters.

    Returns:
        CalculatorOutput: The versioned response with the calculation result.

    Raises:
        ZeroDivisionError: If division by zero is attempted.
    """
    domain_request = CalculationRequest(
        operation=request.type_of_calc, value1=request.value1, value2=request.value2
    )
    domain_result = calculate_domain(domain_request)
    return CalculatorOutput(result=domain_result.result)
