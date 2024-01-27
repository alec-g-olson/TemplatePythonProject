"""Dataclasses used for calculations."""

from enum import Enum

from pydantic import BaseModel


class CalculationType(Enum):
    """Enum representing types of calculations."""

    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4

    def __str__(self):
        """Return the name of this enum to represent it as a string."""
        return self.name


class CalculatorInput(BaseModel):
    """Object containing the information required to do a calculation."""

    typeOfCalc: CalculationType
    value1: float
    value2: float


class CalculatorOutput(BaseModel):
    """Object containing the information resulting from a calculation."""

    result: float
