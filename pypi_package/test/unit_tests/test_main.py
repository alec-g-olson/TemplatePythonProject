"""Tests for the CLI entrypoint."""

from argparse import Namespace
from pathlib import Path

from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.data_models import CalculationType
from template_python_project.main import parse_args, run_main


def test_parser(tmp_path: Path) -> None:
    """parse_args converts CLI strings into the expected Namespace."""
    input_file = tmp_path.joinpath("in.json")
    output_file = tmp_path.joinpath("out.json")
    parsed_args = parse_args(
        args=["--input", str(input_file), "--output", str(output_file)]
    )
    assert parsed_args == Namespace(input=input_file, output=output_file)


def test_main(tmp_path: Path) -> None:
    """run_main writes the correct JSON result to the output file."""
    input_file = tmp_path.joinpath("in.json")
    output_file = tmp_path.joinpath("out.json")
    request = CalculatorInput(type_of_calc=CalculationType.ADD, value1=5.55, value2=10)
    input_file.write_text(request.model_dump_json())
    run_main(Namespace(input=input_file, output=output_file))
    with output_file.open() as result_reader:
        observed_output = CalculatorOutput.model_validate_json(result_reader.read())
    assert observed_output == CalculatorOutput(result=15.55)
