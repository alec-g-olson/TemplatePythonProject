Source Code Style Guide
=======================

This guide describes the conventions, patterns, and principles used to write source code
in this project.  It covers everything from how to divide a package into subpackages down
to how to name a local variable.  When in doubt about any structural or stylistic
decision, consult this document.

The automated enforcement tools — Ruff, mypy, and Bandit — catch most surface-level
issues.  This guide addresses the design-level decisions that tools cannot check.

Architecture
------------

Layered Structure
~~~~~~~~~~~~~~~~~

Every subproject with non-trivial logic is organized into layers.  Dependencies may only
flow **downward**; a lower layer may never import from a higher one.

.. code-block:: text

    CLI / Entrypoints        ← parses args, reads/writes files
           ↓
    API layer                ← public contracts enforced by versioned models,
           ↓                     translation to internal types, single call to a domain
    Domain engines          ← business logic, algorithms, orchestration;
           ↓                   communicate via dataclasses
    Utilities / Persistence  ← shared types and type aliases, pure helpers,
                                file I/O, static resources, some persistent blobs may
                                be versioned

**CLI / Entrypoints** are thin wrappers.  They parse arguments, read input from disk,
call into the API layer, and write output to disk.  They contain no business logic.

**The API layer** is the translation boundary between the external world and the
internal domain.  It defines versioned request/response models, validates incoming data,
extracts the necessary values from those models, arranges them into plain dataclasses and
primitive values, and calls exactly **one** function from the top-level domain.  It then
wraps that function's return value in the appropriate versioned output model.  The API
layer's versioned models never travel further than the API layer itself.

**Domain packages** implement the algorithms and orchestration logic of the software.
They are organized into focused subpackages, each owning a clearly-defined
responsibility.  They communicate with each other exclusively through dataclasses and
plain values — never through versioned API models.  A domain package may define
dataclasses that other packages instantiate and pass back to it; this is the correct way
for domain packages to collaborate without creating circular dependencies.

**Utilities and persistence** are the lowest layer.  Utilities contain shared domain
types and type aliases (``EmailAddress``, ``CurrencyCode``) and pure helpers (string
manipulation, math).  Persistence is responsible solely for I/O: reading files, writing
files, querying external services.  Neither contains business logic.  When writing blobs
to and from persistent storage using versioned models is appropriate.

Subpackage Responsibilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each subpackage owns a single, clearly-named responsibility.  The responsibility should
be expressible in one sentence.  If it takes more than one sentence, the subpackage is
doing too much.

Subpackages define their own dataclasses in a ``data_models.py`` file when they need to
pass structured data to or from their functions.  These dataclasses are part of that
subpackage's interface: another package that wants to call a function in this subpackage
may need to construct one of its dataclasses first.  That is intentional and correct —
the dataclass represents a self-contained concept that belongs to the package that owns
the function.

No Circular Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Circular imports are always a sign of a design problem.  If module A needs something from
module B and module B needs something from module A, one of the following is usually true:

* The shared thing belongs in a separate, lower-level module that both can import from.
* One of the modules is doing too much and should be split.

Resolve the circular dependency rather than working around it.

Functions and Classes
---------------------

Prefer Pure Functions
~~~~~~~~~~~~~~~~~~~~~

A pure function returns a value that depends only on its arguments and has no observable
side effects.  Pure functions are easy to test (no setup or teardown), easy to reason
about (the signature is the complete contract), and easy to compose.

Use pure functions for:

* Business logic and algorithms
* Data transformations and computations
* Configuration resolution
* Utility operations (string manipulation, math)

.. code-block:: python

    # Good: pure function, all dependencies explicit
    def convert_currency(
        amount: Decimal,
        exchange_rate: ExchangeRate,
        rounding_mode: RoundingMode,
    ) -> Decimal:
        ...

Use Classes When State Is Required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A class is appropriate when state must persist across multiple operations — for example,
a network client that holds a connection, or a calculator that is initialized once with
configuration and then called many times.

Do not create a class just to group related functions.  A module already groups related
functions.  A class that contains only static or class methods is almost always better
expressed as a module of top-level functions.

When a class is appropriate:

* Initialize it once with its configuration.
* Pass it as a parameter to the functions that need it.
* Do not reach up the call stack to access global instances.

.. code-block:: python

    # Good: class holds state (the configured client); passed as a parameter
    class SomeServiceClient:
        def __init__(self, endpoint: str, timeout: int) -> None:
            self._client = httpx.Client(base_url=endpoint, timeout=timeout)

        def some_request(self, request: SomeRequest) -> SomeResponse:
            ...

    # At the API layer:
    def run_analysis(params: AnalysisParameters) -> AnalysisOutput:
        client = SomeServiceClient(
            endpoint=params.service_endpoint,
            timeout=params.timeout,
        )
        return _core_analysis(params=params, client=client)

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

Pass dependencies as arguments rather than constructing them inside functions.  This
makes tests easier to write (callers can supply controlled instances) and makes the
contract of each function explicit (the signature tells you exactly what it needs).

Domain functions receive what they need as parameters and do not reach outside their own
scope to obtain it.  When a dependency is genuinely stateful (a network client, a
configured service), it should be constructed and configured by the caller and passed in.

.. code-block:: python

    # Good: the caller constructs the stateful dependency and passes it in
    def generate_report(
        records: list[Record],
        report_config: ReportConfig,
        client: SomeServiceClient,
    ) -> list[Result]:
        ...

    # Bad: dependency constructed inside a function that should not own it
    def generate_report(
        records: list[Record],
        report_config: ReportConfig
    ) -> list[Result]:
        client = SomeServiceClient(endpoint=HARDCODED_URL)  # hidden dependency
        ...

Data Models
-----------

There are two kinds of structured types in this codebase: **versioned Pydantic models**
at the API boundary, and **dataclasses** everywhere else.  These serve different purposes
and must not be confused.

Versioned API Models
~~~~~~~~~~~~~~~~~~~~~

``VersionedModel`` is used for exactly two things:

1. Validating data that arrives from outside the package (deserializing a JSON request).
2. Presenting results back to the outside world (serializing a JSON response).

Versioned models never enter the domain engins or utility packages, they belong to their
respective API and persistence layers.  Once the API or persistence layer has validated
an incoming model, it extracts the values it needs and moves on.  Domain functions never
accept or return versioned models.

``VersionedModel`` provides:

* A ``data_model_version`` field that is automatically populated from
  ``current_version`` when the model is instantiated, so callers never have to specify
  it.
* Validation that rejects versions outside the supported range
  (``lowest_supported_version`` to ``current_version``).
* A ``_coerce_to_most_recent_version`` model validator for migration logic.

When you add a new field to an existing versioned model:

1. Bump ``current_version``.
2. Update ``lowest_supported_version`` only when dropping support for an old version is
   intentional and deliberate.
3. Implement migration logic in ``_coerce_to_most_recent_version`` so that existing
   serialized payloads at older versions can be loaded and coerced forward.

.. code-block:: python

    class OrderInput(VersionedModel):
        current_version: ClassVar[Version] = Version(major=1, minor=1, patch=0)
        lowest_supported_version: ClassVar[Version] = Version(major=1, minor=0, patch=0)

        @model_validator(mode="before")
        @classmethod
        def _coerce_to_most_recent_version(cls, data: Any) -> Any:
            version = cls._get_valid_version_if_any_from_raw_data(data=data)
            if version is not None and version <= Version(major=1, minor=0, patch=0):
                data["new_field"] = "sensible_default"
                data["data_model_version"] = "1.1.0"
            return data

    # In the API service function:
    def process_order(params: OrderInput) -> OrderOutput:
        # Translate from versioned model to plain values, then call the domain.
        total = compute_order_total(
            items=params.items,
            pricing_config=PricingConfig(
                currency=params.currency,
                discount_rate=params.discount_rate,
            ),
        )
        return OrderOutput(total=total)

Dataclasses
~~~~~~~~~~~

Dataclasses are the standard way to pass structured, self-contained concepts between
functions.  They are lightweight, readable, and carry no serialization overhead.

Use dataclasses whenever a function needs to pass or receive a group of values that
belong together as a concept.  Dataclasses can cross package boundaries: if package B
needs to call a function in package A that expects an ``AConfig`` dataclass, package B
imports ``AConfig`` from package A, constructs it, and passes it in.  This is how domain
packages collaborate — not by sharing versioned models, but by sharing dataclasses.

Use ``frozen=True`` for dataclasses that represent configuration or parameters.  Mutation
of these objects after construction is a frequent source of subtle bugs.

.. code-block:: python

    @dataclass(frozen=True)
    class PricingConfig:
        rate_table: RateTable
        currency: str | None

    # Another package constructs and passes this dataclass:
    config = PricingConfig(rate_table=load_rate_table("us"), currency="USD")
    total = compute_order_total(items=items, pricing_config=config)

Do not use Pydantic models for internal types.  Their validation machinery is valuable at
the serialization boundary, but it adds complexity without benefit inside the domain.

Shared Domain Types and Type Aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some domain concepts are so fundamental that they are used across multiple packages.
``EmailAddress``, ``CurrencyCode``, ``Percentage`` — these do not belong to any single
subpackage; they belong to a shared utility package.

Define these types once, in the utility package, and import them everywhere.  Do not
redefine the same concept in multiple packages.

When a raw Python type (``str``, ``dict``, ``float``) carries domain-specific
constraints, encode those constraints in an ``Annotated`` type alias with a
``BeforeValidator``:

.. code-block:: python

    # In a shared utilities module:
    EmailAddress = Annotated[str, BeforeValidator(_validate_and_normalize_email)]
    RateTable = Annotated[dict[str, float], BeforeValidator(_validate_rate_entries)]

Use these aliases throughout the codebase instead of raw ``str`` or ``dict``.  This
ensures that validated types are self-documenting and that the same validation logic is
applied consistently everywhere, without being duplicated.

Immutability
~~~~~~~~~~~~

Prefer immutable data.  Use ``frozen=True`` on dataclasses that represent configuration
or parameters.  Mutation of these objects after construction is a frequent source of
subtle bugs.

Prefer Enums Over Strings and Booleans
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a parameter can take one of a fixed set of values, use an enum.

.. code-block:: python

    # Good
    class OutputFormat(StrEnum):
        JSON = "json"
        CSV = "csv"
        XML = "xml"

    def generate_report(output_format: OutputFormat) -> ReportResult: ...

    # Bad
    def generate_report(output_format: str) -> ReportResult: ...

Avoid boolean parameters when the two states would be better expressed as two distinct
function signatures or an enum.  A function with a ``reverse=True`` argument usually
wants to be two functions, or an enum with two members.

CLI Entrypoints
---------------

Every CLI script follows a three-part structure:

.. code-block:: python

    def parse_args(args: list[str] | None = None) -> Namespace:
        """Builds and returns the argument parser result.

        Args:
            args (list[str] | None): Arguments to parse.  When ``None``, reads from
                ``sys.argv[1:]``.  Pass an explicit list in tests.

        Returns:
            Namespace: Parsed arguments.
        """
        parser = ArgumentParser(description="...")
        parser.add_argument("--input", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        return parser.parse_args(args=args)


    def run_main(args: Namespace) -> None:
        """Reads input, calls the API, and writes output.

        Args:
            args (Namespace): Parsed arguments from ``parse_args()``.
        """
        request = RequestModel.model_validate_json(args.input.read_text())
        result = api_service_function(request=request)
        args.output.write_text(result.model_dump_json(indent=2))


    if __name__ == "__main__":  # pragma: no cov
        run_main(args=parse_args())

The ``parse_args()`` function accepts an optional ``args`` list so that tests can invoke
it without patching ``sys.argv``.  The ``if __name__ == "__main__"`` guard and the
``parse_args()`` call with no arguments are excluded from coverage because they cannot
be meaningfully tested.  ``run_main()`` is fully testable and must have 100% coverage.

``run_main()`` contains only I/O: reading inputs, calling into the API layer, and writing
outputs.  It contains no business logic.

Type Annotations
----------------

All functions and methods must have complete type annotations: every parameter and the
return type.  This is enforced by mypy in strict mode.

Use the most specific type available.  Prefer ``Path`` over ``str`` for file paths;
prefer a domain-specific ``Annotated`` type over its underlying primitive; prefer a
concrete collection type (``list[str]``) over an abstract one (``Sequence[str]``) in
return types.

Do not use ``Any`` except where it is unavoidable (e.g., when parsing raw JSON before
validation), and always accompany it with a ``type: ignore[...]`` comment explaining why.

.. code-block:: python

    # Good
    def load_config(config_id: str) -> AppConfig: ...

    # Bad
    def load_config(config_id):  # no annotations
        ...

    def load_config(config_id: str) -> dict:  # too broad
        ...

Docstrings
----------

Every public module, class, function, and method must have a docstring.  Use
**Google-style docstrings** throughout.

Module Docstrings
~~~~~~~~~~~~~~~~~

Package ``__init__.py`` files and top-level modules describe their purpose and then list
their contents:

.. code-block:: python

    """Top-level package for the application.

    SubPackages:
        | calculators: Calculation domain engine and data models.
        | api: Public request/response models and service functions.
        | versioned_model: Pydantic base model and semver type for versioned schemas.

    Modules:
        | main: CLI entry point for calculations.
    """

Modules that are not packages list their attributes (module-level constants and
non-function, non-class definitions):

.. code-block:: python

    """Numeric constants used for tax computation.

    Attributes:
        DEFAULT_TAX_RATE (float): Default tax rate, stored here as source of truth.
    """

Function and Method Docstrings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def convert_currency(
        amount: Decimal,
        exchange_rate: ExchangeRate,
        rounding_mode: RoundingMode,
    ) -> Decimal:
        """Convert a monetary amount from one currency to another.

        Multiplies ``amount`` by the rate in ``exchange_rate`` and rounds the
        result according to ``rounding_mode``.

        Args:
            amount (Decimal): The monetary amount to convert.
            exchange_rate (ExchangeRate): The exchange rate and currency metadata.
            rounding_mode (RoundingMode): How to round the converted amount.

        Returns:
            Decimal: The converted monetary amount.

        Raises:
            ValueError: If ``amount`` is negative.
        """

Required sections:

* **Args** — for every parameter, including ``self``.  Give the type in parentheses and
  a description on the same line.  Use a hanging indent for multi-line descriptions.
* **Returns** — describe the return value.  Omit for ``None``-returning functions only
  if the function's purpose makes the lack of return value obvious.
* **Raises** — list every exception the caller might need to handle.
* **Yields** — for generators, in place of Returns.

Use backticks (````like_this````) for references to code: parameter names, attribute
names, other functions, and type names.  Use ``r"""..."""`` when the docstring contains
backslashes.

Naming
------

Follow PEP 8 for all names:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Element
     - Convention
     - Example
   * - Module / package
     - ``snake_case``
     - ``currency_converter.py``
   * - Class
     - ``PascalCase``
     - ``ExchangeRate``
   * - Function / method
     - ``snake_case``
     - ``convert_currency``
   * - Parameter / variable
     - ``snake_case``
     - ``rounding_mode``
   * - Module-level constant
     - ``UPPER_SNAKE_CASE``
     - ``DEFAULT_TAX_RATE``
   * - Private function / method
     - ``_leading_underscore``
     - ``_validate_email``
   * - Type alias
     - ``PascalCase``
     - ``EmailAddress``
   * - Enum class
     - ``PascalCase``
     - ``OutputFormat``
   * - Enum member
     - ``UPPER_SNAKE_CASE``
     - ``OutputFormat.CSV``

Name things for what they **are**, not for what they do or how they work.  A function
that returns the configuration for a region is ``get_region_config``, not
``do_config_lookup`` or ``fetch_yaml_and_parse``.  A variable that holds a random number
generator is ``rng``, not ``my_random`` or ``r``.

Use full words.  Abbreviations are acceptable only when they are universal in the domain
(``id``, ``url``, ``uuid``) or when they are part of a well-established acronym
(``rng``, ``api``, ``csv``).

Module-Level Constants
----------------------

Magic numbers and magic strings are prohibited.  Any literal value with domain meaning
must be given a name:

.. code-block:: python

    # Bad
    if len(country_code) != 2:
        raise ValueError("Country code must be exactly 2 characters")

    # Good
    COUNTRY_CODE_LENGTH = 2

    if len(country_code) != COUNTRY_CODE_LENGTH:
        raise ValueError(f"Country code must be exactly {COUNTRY_CODE_LENGTH} characters")

Constants live at the top of the module that owns them, before any function or class
definitions.  If a constant is used by more than one module, move it to the lowest-level
module that all consumers already import, or to a dedicated constants module.

Static Resources
----------------

Data files that are distributed as part of the package (lookup tables, default
configurations, reference data) live in a ``resources/`` subdirectory of the
subpackage that owns them:

.. code-block:: text

    pricing/
        resources/
            rate_tables/
                us.yaml
                eu.yaml
        resource_loader.py   ← the only module that reads these files

The resource loader module is the sole consumer of the files in ``resources/``.  No
other module in the subpackage reads from disk; they call the resource loader instead.
This isolates I/O from business logic and makes it possible to test the business logic
without touching the file system.

Automated Enforcement
---------------------

The following tools run automatically as part of ``make test`` and must all pass before
a pull request can be merged.  Their configuration lives in ``pyproject.toml``.

**Ruff** — formats and lints all Python files.  We enable all stable rules and turn off
only those that are genuinely inapplicable to this codebase.  Pydocstyle is configured
to require Google-style docstrings.

**mypy** — runs in strict mode.  All functions must be typed; ``Any`` is prohibited
except where unavoidable; generic types must be parameterized.

**Bandit** — scans source files for security issues.  Low-severity findings may be
suppressed with a ``# nosec`` comment only if the exact rule ID is given and a
justification is provided.

Use of suppression comments (``# noqa``, ``# type: ignore``, ``# nosec``,
``# pragma: no cover``) in reviewed code must include the specific code being suppressed
and a clear reason.  Reviewers are required to scrutinize every suppression.