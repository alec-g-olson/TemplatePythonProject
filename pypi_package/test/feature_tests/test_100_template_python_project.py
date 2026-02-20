"""Feature tests for ticket 100 calculator CLI behavior."""

from pathlib import Path
from subprocess import PIPE, Popen

import pytest
from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.data_models import CalculationType


@pytest.mark.parametrize(
    ("calculator_input", "expected_output"),
    [
        (
            CalculatorInput(type_of_calc=CalculationType.ADD, value1=5.5, value2=10),
            CalculatorOutput(result=15.5),
        ),
        (
            CalculatorInput(
                type_of_calc=CalculationType.SUBTRACT, value1=10, value2=5.5
            ),
            CalculatorOutput(result=4.5),
        ),
        (
            CalculatorInput(type_of_calc=CalculationType.MULTIPLY, value1=3, value2=7),
            CalculatorOutput(result=21.0),
        ),
        (
            CalculatorInput(type_of_calc=CalculationType.DIVIDE, value1=10, value2=4),
            CalculatorOutput(result=2.5),
        ),
    ],
)
def test_main_cli_writes_expected_output_for_each_calculation_type(
    calculator_input: CalculatorInput,
    expected_output: CalculatorOutput,
    staged_main_command: list[str],
    staged_python_env: dict[str, str],
    tmp_path: Path,
) -> None:
    """Run the staged CLI with Popen and assert the output JSON is correct."""
    calculation_type_name = calculator_input.type_of_calc.name.lower()
    input_file = tmp_path.joinpath(f"{calculation_type_name}_input.json")
    output_file = tmp_path.joinpath(f"{calculation_type_name}_result.json")
    input_file.write_text(calculator_input.model_dump_json())
    cmd = Popen(
        args=[
            *staged_main_command,
            "--input",
            str(input_file),
            "--output",
            str(output_file),
        ],
        env=staged_python_env,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    _, stderr = cmd.communicate()
    assert cmd.returncode == 0, stderr

    observed_output = CalculatorOutput.model_validate_json(output_file.read_text())
    assert observed_output == expected_output


def test_main_cli_fails_for_divide_by_zero(
    staged_main_command: list[str], staged_python_env: dict[str, str], tmp_path: Path
) -> None:
    """Division by zero exits non-zero and does not produce an output file."""
    input_file = tmp_path.joinpath("divide_by_zero_input.json")
    output_file = tmp_path.joinpath("divide_by_zero_result.json")
    divide_by_zero_input = CalculatorInput(
        type_of_calc=CalculationType.DIVIDE, value1=5, value2=0
    )
    input_file.write_text(divide_by_zero_input.model_dump_json())
    cmd = Popen(
        args=[
            *staged_main_command,
            "--input",
            str(input_file),
            "--output",
            str(output_file),
        ],
        env=staged_python_env,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    _, stderr = cmd.communicate()
    assert cmd.returncode != 0
    assert "ZeroDivisionError" in stderr
    assert not output_file.exists()
