"""Module that provides a CLI for calculations."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from template_python_project.calculators.calculator import calculate_result
from template_python_project.calculators.data_models import (
    CalculationType,
    CalculatorInput,
)


def parse_args(args: list[str] | None = None) -> Namespace:
    """Build the argument parser used by this program's main method.

    Args:
        args (list[str] | None): Args to parse.  Defaults to None, causing
            sys.argv[1:] to be used.  This arg exists to make testing easy.

    Returns:
        Namespace: An object with fields parsed from the command line.
    """
    parser = ArgumentParser(
        description="Takes 2 numbers and a calculation type to report the result."
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=[str(x) for x in CalculationType],
        help="The type of calculation to do.",
    )
    parser.add_argument(
        "--val1", type=float, help="The first value to use in calculation."
    )
    parser.add_argument(
        "--val2", type=float, help="The second value to use in calculation."
    )
    parser.add_argument(
        "--out-file", type=Path, help="The location of the output file."
    )
    return parser.parse_args(args=args)


def run_main(args: Namespace) -> None:
    """Run this program.

    In reality this is a "sub-main" method that we broke out in order to test.

    Args:
        args (Namespace): A namespace that has been parsed from the command line.

    Returns:
        None

    """
    input_vals = CalculatorInput(
        type_of_calc=CalculationType[args.type], value1=args.val1, value2=args.val2
    )
    output = calculate_result(input_vals)
    with args.out_file.open("w") as out_writer:
        out_writer.write(output.model_dump_json())


if __name__ == "__main__":  # pragma: no cov
    run_main(args=parse_args())
