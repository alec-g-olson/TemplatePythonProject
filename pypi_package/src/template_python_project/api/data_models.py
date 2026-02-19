"""Versioned API data models for calculator service.

These models define the public contract at the API boundary. They use semantic
versioning to support schema evolution while maintaining backwards compatibility.

Classes:
    CalculatorInput: Versioned request model for API clients.
    CalculatorOutput: Versioned response model for API clients.
"""

from typing import ClassVar

from semver import Version

from template_python_project.api.versioned_model.versioned_model import VersionedModel
from template_python_project.calculators.data_models import CalculationType


class CalculatorInput(VersionedModel):
    """Versioned request model for calculator API.

    Attributes:
        type_of_calc (CalculationType): The operation to perform.
        value1 (float): The first operand.
        value2 (float): The second operand.
        data_model_version (str): The version of this model.
    """

    current_version: ClassVar[Version] = Version(major=1, minor=0, patch=0)

    type_of_calc: CalculationType
    value1: float
    value2: float


class CalculatorOutput(VersionedModel):
    """Versioned response model for calculator API.

    Attributes:
        result (float): The result of the calculation.
        data_model_version (str): The version of this model.
    """

    current_version: ClassVar[Version] = Version(major=1, minor=0, patch=0)

    result: float
