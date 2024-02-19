"""Module implementing calculator logic."""

from template_python_project.calculators.data_models import (
    CalculationType,
    CalculatorInput,
    CalculatorOutput,
)


def calculate_result(args: CalculatorInput) -> CalculatorOutput:
    """Perform calculation based on the inputs.

    Arguments:
      args (CalculatorInput): Input for calculation.

    Returns:
      CalculatorOutput: Output of the calculation.
    """
    if args.typeOfCalc == CalculationType.ADD:
        result = args.value1 + args.value2
    elif args.typeOfCalc == CalculationType.SUBTRACT:
        result = args.value1 - args.value2
    elif args.typeOfCalc == CalculationType.MULTIPLY:
        result = args.value1 * args.value2
    else:
        result = args.value1 / args.value2
    return CalculatorOutput(result=result)
