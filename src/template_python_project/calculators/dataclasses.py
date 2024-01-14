"""Dataclasses used for calculations."""
from dataclasses import dataclass
from enum import Enum

from dataclasses_json import dataclass_json


class CalculationType(Enum):
    """Enum representing types of calculations."""

    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4

    def __str__(self):
        """Return the name of this enum to represent it as a string."""
        return self.name


@dataclass_json
@dataclass
class CalculatorInput:
    """Object containing the information required to do a calculation."""

    typeOfCalc: CalculationType
    value1: float
    value2: float


@dataclass_json
@dataclass
class CalculatorOutput:
    """Object containing the information resulting from a calculation."""

    result: float
