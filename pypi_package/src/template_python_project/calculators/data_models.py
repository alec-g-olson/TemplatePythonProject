"""Domain data models and enums for calculations.

Attributes:
    CalculationType: Enum of supported calculation operations.
    CalculationRequest: Input dataclass for the calculation domain.
    CalculationResult: Output dataclass from the calculation domain.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import override


class CalculationType(StrEnum):
    """Enum representing types of calculations."""

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"

    @override
    def __str__(self) -> str:
        """Return the name of this enum to represent it as a string.

        Returns:
            str: A string representation of the enum. (name)
        """
        return self.name


@dataclass(frozen=True)
class CalculationRequest:
    """Input parameters for a calculation operation."""

    operation: CalculationType
    value1: float
    value2: float


@dataclass(frozen=True)
class CalculationResult:
    """Result of a calculation operation."""

    result: float
