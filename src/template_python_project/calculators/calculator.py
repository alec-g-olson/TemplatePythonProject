"""Module implementing calculator logic."""
from template_python_project.calculators.dataclasses import (
    CalculationType,
    CalculatorInput,
    CalculatorOutput,
)


def calculate_result(args: CalculatorInput) -> CalculatorOutput:
    """Perform calculation based on the inputs."""
    result = float("Nan")
    match args.typeOfCalc:
        case CalculationType.ADD:
            result = args.value1 + args.value2
        case CalculationType.SUBTRACT:
            result = args.value1 - args.value2
        case CalculationType.MULTIPLY:
            result = args.value1 * args.value2
        case CalculationType.DIVIDE:
            result = args.value1 / args.value2
    return CalculatorOutput(result=result)
