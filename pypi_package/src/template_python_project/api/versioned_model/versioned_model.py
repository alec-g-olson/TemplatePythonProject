"""Base class for Pydantic models with semantic versioning and migration support.

Provides ``VersionedModel``, an abstract ``BaseModel`` subclass that stamps every
instance with a ``data_model_version`` field and validates that the version falls
within the range each concrete subclass declares.  Subclasses can override
``_coerce_to_most_recent_version`` to migrate payloads produced by older code.

Classes:
    | VersionedModel: Abstract base for versioned Pydantic models.
"""

from abc import ABC
from collections.abc import Callable
from typing import Any, ClassVar, Literal, override

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.main import IncEx
from semver import Version

from template_python_project.api.versioned_model.pydantic_semver_annotation import (
    PydanticSemVer,
)


class VersionedModel(BaseModel, ABC):
    """Abstract base for Pydantic models that carry a semantic version.

    Concrete subclasses must set ``current_version`` and optionally
    ``lowest_supported_version``.  Validation ensures that every incoming
    ``data_model_version`` falls within ``[lowest_supported_version, current_version]``.
    When no version is supplied, ``current_version`` is assumed.

    Override ``_coerce_to_most_recent_version`` in subclasses to backfill fields
    added in newer schema versions so that old payloads validate successfully.

    Serialization defaults are changed from Pydantic's built-ins:
    ``model_dump`` defaults to ``mode="json"`` and ``serialize_as_any=True``,
    and ``model_dump_json`` defaults to ``serialize_as_any=True``.
    """

    model_config = ConfigDict(extra="forbid")

    current_version: ClassVar[Version]
    lowest_supported_version: ClassVar[Version] = Version(major=1, minor=0, patch=0)

    data_model_version: PydanticSemVer = Field(default=None, validate_default=True)  # type: ignore[assignment]

    @field_validator("data_model_version", mode="before")
    @classmethod
    def _version_not_none(cls, value: Any) -> Any:  # noqa: ANN401
        """Default ``data_model_version`` to ``current_version`` when not supplied.

        Internal code never needs to specify a version explicitly; only external
        payloads from older code versions carry an explicit version string.

        Args:
            value (Any): The raw value for ``data_model_version``.

        Returns:
            Any: ``current_version`` if ``value`` is ``None``, otherwise ``value``
                unchanged.
        """
        if value is None:
            return cls.current_version
        return value

    @field_validator("data_model_version", mode="after")
    @classmethod
    def _valid_version(cls, value: Version) -> Version:
        """Reject versions outside ``[lowest_supported_version, current_version]``.

        Args:
            value (Version): The parsed semantic version.

        Returns:
            Version: The validated version.

        Raises:
            ValueError: If ``value`` is below ``lowest_supported_version`` or above
                ``current_version``.
        """
        if value < cls.lowest_supported_version:
            msg = (
                f"Model undefined for versions lower than "
                f"'{cls.lowest_supported_version}', '{value}' is not valid."
            )
            raise ValueError(msg)
        if value > cls.current_version:
            msg = (
                f"Model undefined for versions greater than '{cls.current_version}', "
                f"'{value}' is not valid."
            )
            raise ValueError(msg)
        return value

    @classmethod
    def _get_valid_version_if_any_from_raw_data(
        cls,
        data: Any,  # noqa: ANN401
    ) -> Version | None:
        """Extract and validate a version from raw input data, if present.

        Returns the parsed ``Version`` only when ``data`` is a dict containing a
        ``data_model_version`` key whose value is a valid semver string (or
        ``Version`` instance) within the supported range.  Returns ``None`` in
        every other case without raising.

        Args:
            data (Any): The raw data being validated by Pydantic.

        Returns:
            Version | None: The parsed version if valid, otherwise ``None``.
        """
        if isinstance(data, dict) and "data_model_version" in data:
            try:
                if isinstance(data["data_model_version"], Version):
                    version = data["data_model_version"]
                else:
                    version = Version.parse(data["data_model_version"])
                if cls.lowest_supported_version <= version <= cls.current_version:
                    return version
            except ValueError:
                pass
        return None

    @override
    def model_dump(
        self,
        *,
        mode: str = "json",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = True,
    ) -> dict[str, Any]:
        """Serialize the model to a dict, defaulting to JSON mode with duck-typing.

        Overrides Pydantic's ``model_dump`` so that ``mode`` defaults to ``"json"``
        and ``serialize_as_any`` defaults to ``True``.  All other parameters are
        forwarded unchanged; see the Pydantic docs for their full descriptions.

        Args:
            mode (str): Serialization mode passed through to Pydantic.
            include (IncEx | None): Fields to include.
            exclude (IncEx | None): Fields to exclude.
            context (Any | None): Serialization context object.
            by_alias (bool | None): Whether to use field aliases.
            exclude_unset (bool): Whether to exclude unset fields.
            exclude_defaults (bool): Whether to exclude default-valued fields.
            exclude_none (bool): Whether to exclude ``None`` fields.
            round_trip (bool): Whether to preserve values for round-tripping.
            warnings (bool | Literal["none", "warn", "error"]): Warning handling mode.
            fallback (Callable[[Any], Any] | None): Fallback serializer callback.
            serialize_as_any (bool): Whether to enable duck-typed serialization.

        Returns:
            dict[str, Any]: A dictionary representation of the model.
        """
        return super().model_dump(
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            context=context,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    @override
    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = True,
    ) -> str:
        """Serialize the model to a JSON string, defaulting to duck-typing.

        Overrides Pydantic's ``model_dump_json`` so that ``serialize_as_any``
        defaults to ``True``.  All other parameters are forwarded unchanged;
        see the Pydantic docs for their full descriptions.

        Args:
            indent (int | None): Pretty-print indentation level.
            include (IncEx | None): Fields to include.
            exclude (IncEx | None): Fields to exclude.
            context (Any | None): Serialization context object.
            by_alias (bool | None): Whether to use field aliases.
            exclude_unset (bool): Whether to exclude unset fields.
            exclude_defaults (bool): Whether to exclude default-valued fields.
            exclude_none (bool): Whether to exclude ``None`` fields.
            round_trip (bool): Whether to preserve values for round-tripping.
            warnings (bool | Literal["none", "warn", "error"]): Warning handling mode.
            fallback (Callable[[Any], Any] | None): Fallback serializer callback.
            serialize_as_any (bool): Whether to enable duck-typed serialization.

        Returns:
            str: A JSON string representation of the model.
        """
        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    @model_validator(mode="before")
    @classmethod
    def _coerce_to_most_recent_version(cls, data: Any) -> Any:  # noqa: ANN401
        """Pre-validation hook for migrating payloads from older schema versions.

        Runs before field validation.  The base implementation is a no-op.
        Subclasses should override this method to backfill fields that were added
        in newer versions so that older payloads validate successfully.

        Args:
            data (Any): Raw data being validated by Pydantic.

        Returns:
            Any: The data, potentially mutated to match ``current_version``.
        """
        version = cls._get_valid_version_if_any_from_raw_data(data=data)
        if version is not None and version < cls.current_version:
            pass
        return data
