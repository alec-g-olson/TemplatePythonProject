from typing import Callable


def empty_function() -> None:  # pragma: no cover, exists only for return bytecode
    return


EMPTY_FUNCTION_BYTECODE = empty_function.__code__.co_code


def empty_function_with_docstring() -> None:  # pragma: no cover, same as above
    """A docstring"""
    return


EMPTY_FUNCTION_WITH_DOCSTRING_BYTECODE = empty_function_with_docstring.__code__.co_code
ALL_EMPTY_FUNCTION_BYTECODES = [
    EMPTY_FUNCTION_BYTECODE,
    EMPTY_FUNCTION_WITH_DOCSTRING_BYTECODE,
]


def is_an_empty_function(func: Callable) -> bool:
    return func.__code__.co_code in ALL_EMPTY_FUNCTION_BYTECODES
