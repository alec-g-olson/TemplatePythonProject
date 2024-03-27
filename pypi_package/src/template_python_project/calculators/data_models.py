"""Data models used for calculations."""

from enum import Enum

from pydantic import BaseModel


class CalculationType(str, Enum):
    """Enum representing types of calculations."""

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"


class CalculatorInput(BaseModel):
    """Object containing the information required to do a calculation."""

    type_of_calc: CalculationType
    value1: float
    value2: float


class CalculatorOutput(BaseModel):
    """Object containing the information resulting from a calculation."""

    result: float
