from argparse import Namespace
from pathlib import Path

from template_python_project.calculators.data_models import CalculatorOutput
from template_python_project.main import parse_args, run_main


def test_parser(tmp_path: Path) -> None:
    calc_type = "ADD"
    val1 = 5.55
    val2 = 10
    out_file = tmp_path.joinpath("out.json")
    parsed_args = parse_args(
        args=[
            str(x)
            for x in [
                "--type",
                calc_type,
                "--val1",
                val1,
                "--val2",
                val2,
                "--out-file",
                out_file,
            ]
        ]
    )
    assert parsed_args == Namespace(
        type=calc_type, val1=val1, val2=val2, out_file=out_file
    )


def test_main(tmp_path: Path) -> None:
    out_file = tmp_path.joinpath("out.json")
    run_main(Namespace(type="ADD", val1=5.55, val2=10, out_file=out_file))
    with out_file.open() as result_reader:
        observed_output = CalculatorOutput.model_validate_json(result_reader.read())
    assert observed_output == CalculatorOutput(result=15.55)
