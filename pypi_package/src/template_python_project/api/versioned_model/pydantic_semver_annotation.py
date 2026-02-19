"""Pydantic integration for semver ``Version``.

Provides an ``Annotated`` type that validates and serializes semantic versions
in Pydantic models: accepts ``Version`` instances or strings (e.g. ``"1.2.3"``),
and serializes to string in JSON.

Based on the "Handling third-party types" pattern from Pydantic:
https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types

Attributes:
    | PydanticSemVer: Annotated type for semantic versions in Pydantic models.
"""

from typing import Annotated, Any

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticCustomError, core_schema
from semver import Version


def _parse_version(value: str) -> Version:
    """Parse a string into a semver Version, raising a Pydantic error on failure.

    Args:
        value (str): The string to parse as a semantic version.

    Returns:
        Version: The parsed semantic version.
    """
    try:
        return Version.parse(value)
    except ValueError as e:
        err_type = "semver_parse"
        err_msg = "Input is not a valid semantic version string: {msg}"
        raise PydanticCustomError(err_type, err_msg, {"msg": str(e)}) from e


class _SemVerPydanticAnnotation:
    """Annotation that teaches Pydantic how to validate and serialize semver Version."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,  # noqa: ANN401
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """Core schema: accept Version or string; serialize as string.

        Args:
            _source_type (Any): The source type for the schema.
            _handler (GetCoreSchemaHandler): Pydantic's schema handler.

        Returns:
            core_schema.CoreSchema: The core schema for semver validation.
        """
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_version),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(Version), from_str_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """JSON schema: string with format and description for semver.

        Args:
            _core_schema (core_schema.CoreSchema): The core schema.
            handler (GetJsonSchemaHandler): Pydantic's JSON schema handler.

        Returns:
            JsonSchemaValue: The JSON schema for semver.
        """
        base = handler(core_schema.str_schema())
        if isinstance(base, dict):  # pragma: no branch
            base = {
                **base,
                "format": "semver",
                "description": "Semantic version (e.g. 1.2.3, 2.0.0-alpha.1)",
                "examples": ["1.0.0", "2.1.3"],
            }
        return base


PydanticSemVer = Annotated[Version, _SemVerPydanticAnnotation]
