"""Module that provides a CLI for calculations."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from template_python_project.api.api import calculate
from template_python_project.api.data_models import CalculatorInput, CalculatorOutput


def parse_args(args: list[str] | None = None) -> Namespace:
    """Build the argument parser used by this program's main method.

    Args:
        args (list[str] | None): Args to parse.  Defaults to None, causing
            sys.argv[1:] to be used.  This arg exists to make testing easy.

    Returns:
        Namespace: An object with fields parsed from the command line.
    """
    parser = ArgumentParser(
        description=(
            "Reads calculator input from a file and writes the result to a file."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the input JSON file (CalculatorInput format).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output JSON file (CalculatorOutput format).",
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
    request: CalculatorInput = CalculatorInput.model_validate_json(
        args.input.read_text()
    )
    result: CalculatorOutput = calculate(request=request)
    with args.output.open("w") as out_writer:
        out_writer.write(result.model_dump_json())


if __name__ == "__main__":  # pragma: no cov
    run_main(args=parse_args())
