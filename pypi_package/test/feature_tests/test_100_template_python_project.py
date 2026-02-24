"""Feature tests for ticket 100 calculator CLI behavior."""

import pytest
from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.data_models import CalculationType
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


def _cli_command_args(input_filename: str, output_filename: str) -> list[str]:
    """Build command args for the calculator CLI."""
    return [
        "python",
        "-m",
        "template_python_project.main",
        "--input",
        input_filename,
        "--output",
        output_filename,
    ]


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
    default_command_context: FeatureTestCommandContext,
    calculator_input: CalculatorInput,
    expected_output: CalculatorOutput,
) -> None:
    """Check if the CLI produces the expected output for each calculation input."""
    cwd = default_command_context.mock_project_root
    calculation_type_name = calculator_input.type_of_calc.name.lower()
    input_filename = f"{calculation_type_name}_input.json"
    output_filename = f"{calculation_type_name}_result.json"
    input_file = cwd.joinpath(input_filename)
    output_file = cwd.joinpath(output_filename)
    input_file.write_text(calculator_input.model_dump_json())
    return_code, _, stderr = run_command_and_save_logs(
        context=default_command_context,
        command_args=_cli_command_args(input_filename, output_filename),
    )
    assert return_code == 0, stderr
    observed_output = CalculatorOutput.model_validate_json(output_file.read_text())
    assert observed_output == expected_output


def test_main_cli_fails_for_divide_by_zero(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """Division by zero exits non-zero and does not produce an output file."""
    cwd = default_command_context.mock_project_root
    input_filename = "divide_by_zero_input.json"
    output_filename = "divide_by_zero_result.json"
    input_file = cwd.joinpath(input_filename)
    output_file = cwd.joinpath(output_filename)
    divide_by_zero_input = CalculatorInput(
        type_of_calc=CalculationType.DIVIDE, value1=5, value2=0
    )
    input_file.write_text(divide_by_zero_input.model_dump_json())
    return_code, _, stderr = run_command_and_save_logs(
        context=default_command_context,
        command_args=_cli_command_args(input_filename, output_filename),
    )
    assert return_code != 0
    assert "ZeroDivisionError" in stderr
    assert not output_file.exists()
