"""Feature tests for ticket 100 calculator CLI behavior."""

import subprocess
from pathlib import Path

import pytest
from template_python_project.api.data_models import CalculatorInput, CalculatorOutput
from template_python_project.calculators.data_models import CalculationType


def _run_cli_in_prod_docker(
    prod_docker_command_prefix: list[str],
    prod_workdir: str,
    input_filename: str,
    output_filename: str,
) -> subprocess.CompletedProcess[str]:
    """Run the CLI in the prod container with tmp_path mounted at prod_workdir."""
    args = [
        *prod_docker_command_prefix,
        "python",
        "-m",
        "template_python_project.main",
        "--input",
        f"{prod_workdir}/{input_filename}",
        "--output",
        f"{prod_workdir}/{output_filename}",
    ]
    return subprocess.run(args, check=False, capture_output=True, text=True)


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
    prod_docker_command_prefix: list[str],
    prod_workdir: str,
    pypi_feature_test_scratch_path: Path,
) -> None:
    """Check if the CLI produces the expected output for each calculation input."""
    calculation_type_name = calculator_input.type_of_calc.name.lower()
    input_filename = f"{calculation_type_name}_input.json"
    output_filename = f"{calculation_type_name}_result.json"
    input_file = pypi_feature_test_scratch_path.joinpath(input_filename)
    output_file = pypi_feature_test_scratch_path.joinpath(output_filename)
    input_file.write_text(calculator_input.model_dump_json())
    result = _run_cli_in_prod_docker(
        prod_docker_command_prefix=prod_docker_command_prefix,
        prod_workdir=prod_workdir,
        input_filename=input_filename,
        output_filename=output_filename,
    )
    assert result.returncode == 0, result.stderr
    observed_output = CalculatorOutput.model_validate_json(output_file.read_text())
    assert observed_output == expected_output


def test_main_cli_fails_for_divide_by_zero(
    prod_docker_command_prefix: list[str],
    prod_workdir: str,
    pypi_feature_test_scratch_path: Path,
) -> None:
    """Division by zero exits non-zero and does not produce an output file."""
    input_filename = "divide_by_zero_input.json"
    output_filename = "divide_by_zero_result.json"
    input_file = pypi_feature_test_scratch_path.joinpath(input_filename)
    output_file = pypi_feature_test_scratch_path.joinpath(output_filename)
    divide_by_zero_input = CalculatorInput(
        type_of_calc=CalculationType.DIVIDE, value1=5, value2=0
    )
    input_file.write_text(divide_by_zero_input.model_dump_json())
    result = _run_cli_in_prod_docker(
        prod_docker_command_prefix=prod_docker_command_prefix,
        prod_workdir=prod_workdir,
        input_filename=input_filename,
        output_filename=output_filename,
    )
    assert result.returncode != 0
    assert "ZeroDivisionError" in result.stderr
    assert not output_file.exists()
