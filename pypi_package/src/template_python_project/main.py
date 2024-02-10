"""Module that provides a CLI for calculations."""

from argparse import ArgumentParser
from pathlib import Path

from template_python_project.calculators.calculator import calculate_result
from template_python_project.calculators.data_models import (
    CalculationType,
    CalculatorInput,
)


def build_parser():
    """Build the argument parser used by this program's main method."""
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
        "--val1",
        type=float,
        help="The first value to use in calculation.",
    )
    parser.add_argument(
        "--val2",
        type=float,
        help="The second value to use in calculation.",
    )
    parser.add_argument(
        "--out-file", type=Path, help="The location of the output file."
    )
    return parser


def main(args):
    """Run this program.

    In reality this is a "sub-main" method that we broke out in order to test.
    """
    input_vals = CalculatorInput(
        typeOfCalc=CalculationType[args.type], value1=args.val1, value2=args.val2
    )
    output = calculate_result(input_vals)
    with args.out_file.open("w") as out_writer:
        out_writer.write(output.model_dump_json())


if __name__ == "__main__":  # pragma: no cover
    parsed_args = build_parser().parse_args()
    main(args=parsed_args)
