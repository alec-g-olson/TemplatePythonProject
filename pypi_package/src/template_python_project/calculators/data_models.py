"""Data models used for calculations."""

from enum import Enum

from pydantic import BaseModel


class CalculationType(Enum):
    """Enum representing types of calculations."""

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"

    def __str__(self) -> str:
        """Return the name of this enum to represent it as a string.

        Returns:
            str: A string representation of the enum. (name)
        """
        return self.name


class CalculatorInput(BaseModel):
    """Object containing the information required to do a calculation."""

    type_of_calc: CalculationType
    value1: float
    value2: float


class CalculatorOutput(BaseModel):
    """Object containing the information resulting from a calculation."""

    result: float
