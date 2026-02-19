Testing Style Guide
===================

This guide describes the philosophy, structure, and conventions for writing tests in this
project.  It is the authoritative reference for how tests should be written and organized.
When in doubt about a testing decision, consult this document.

Philosophy
----------

Tests in this project exist to give us confidence that the software behaves correctly from
the perspective of the people who use it.  They are not meant to verify that a particular
line of code was executed, or that a particular internal data structure has a particular
shape.  They are meant to verify that, given some input, the software produces the correct
output and side effects.

This philosophy has a concrete consequence: **tests should survive refactoring**.  If the
behavior of a feature has not changed, its tests should not break, even if the
implementation beneath them has been completely rewritten.  Tests that break during
refactoring are a signal that they are coupled too tightly to the implementation.

There are two layers of testing in this project:

* **Feature tests** verify the software from the outside, the way a real user would
  experience it.
* **Unit tests** verify individual modules from their public interface, ensuring every use
  case a module is responsible for is covered.

Both layers require 100% coverage of the code they exercise.

Feature Tests
-------------

What They Test
~~~~~~~~~~~~~~

A feature test verifies a complete, user-facing behavior of the software.  "User-facing"
means whatever interface a real consumer of the software would use.  Today that interface
is a command-line tool; tomorrow it may be an HTTP API; eventually it may be a running
service.  The interface changes, but the principle stays the same: **feature tests interact
with the software the way its users do**.

Feature tests are also acceptance tests.  A ticket is not complete until its feature test
passes, and the feature test is the definitive, executable statement of the ticket's
acceptance criteria.

How They Interact With the Software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**CLI phase (current)**

While the primary interface to our software is a command-line tool, feature tests invoke
that tool as a subprocess.  They pass arguments on the command line and read the output
from files or stdout.  They do not import internal modules and call them directly.

.. code-block:: python

    from subprocess import Popen
    import os

    def test_tool_produces_expected_output(
        cli_script: Path, input_file: Path, output_file: Path
    ) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_path)
        process = Popen(
            args=["python", str(cli_script), "--input", str(input_file),
                  "--output", str(output_file)],
            env=env,
        )
        process.communicate()
        assert process.returncode == 0
        result = OutputModel.model_validate_json(output_file.read_text())
        assert result == expected

**API phase (future)**

When the software exposes an HTTP API, feature tests will call that API using an HTTP
client.  A session-scoped fixture will start the server, wait until it is healthy, and
yield the base URL to every test in the session.  Tests will call real endpoints and
assert on real responses.  They will not call internal functions.

**Live-instance phase (further future)**

When we run a test instance of the service in our infrastructure, feature tests will point
at that instance's URL, which will be provided via a session-scoped fixture.  The tests
themselves will be identical to the API-phase tests; only the fixture changes.

The progression looks like this:

.. code-block:: text

    CLI (subprocess)  →  API (HTTP client, local server)  →  Live instance (HTTP client, remote URL)
          ↑                           ↑                                  ↑
    Feature tests call      Feature tests call              Feature tests call
    the same behavior       the same behavior               the same behavior
    through different       through different               through different
    interfaces              interfaces                      interfaces

Session-Scoped Fixtures for Expensive Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Feature tests frequently require setup that is slow: starting a server, running a pipeline,
building an index, or otherwise producing something that every test in a session needs.
Use ``scope="session"`` on fixtures that perform this work so the cost is paid once.

Tests that share session-scoped fixtures are parameterized at the fixture level, not at
the test level.  This lets pytest run the same suite of assertions against multiple
configurations (e.g., different algorithm settings, different parameter sets) without
duplicating test functions.

.. code-block:: python

    @pytest.fixture(scope="session", params=configuration_list)
    def configured_result(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest) -> Result:
        """Run the tool once per configuration and cache the result for the session."""
        ...

Practical Considerations Specific to :doc:`build_support`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The feature tests for :doc:`build_support` are a specialized case.  Because
``build_support`` is itself a build system, its feature tests simulate running ``make``
commands against mock projects inside Docker containers.  Fixtures create a minimal,
git-tracked copy of the project, manipulate it (add files, make commits, push branches),
and then execute ``make`` commands against it.

This is specific to the nature of ``build_support``.  Feature tests for other subprojects
should be simpler: they primarily invoke CLIs or APIs and assert on their outputs.

File Naming and Location
~~~~~~~~~~~~~~~~~~~~~~~~~

Feature test files live in the ``feature_tests/`` directory of each subproject's test
folder and must follow this naming convention:

.. code-block:: text

    test_{ticket_id}_{project_name}.py

The ticket ID is the first segment of the branch name before the first hyphen, or the
entire branch name when no hyphen is present (e.g., ``42`` from either
``42-add-csv-export`` or ``42``).  The project name is the package name as declared in
``pyproject.toml``.  The build pipeline enforces that this file exists before a pull
request can be merged.

For rare cases where a meaningful test is not feasible (e.g., a pure-performance change
with no observable behavior change), the file must still exist and contain a comment
explaining what validation was performed and why a real test is not possible.  A minimal
passing ``assert True`` test keeps the pipeline check satisfied.

Coverage
~~~~~~~~

All lines in feature test files must be covered.  Dead code in test files is not
acceptable: every helper, every fixture body, and every assertion must execute during a
test run.  Use ``# pragma: no cov`` only with a clear explanation, such as a branch
that is only taken when a test fails, and only with pull request reviewer approval.

Unit Tests
----------

What They Test
~~~~~~~~~~~~~~

A unit test file covers the complete **use cases** of its corresponding source module.  It
is not a line-by-line exercise of implementation details; it is a specification of every
meaningful behavior that the module is responsible for.

The goal is that if the implementation inside the module changes — different data
structures, different algorithms, different internal helpers — but the module still
satisfies its use cases, then the unit tests still pass.

One-to-One Correspondence With Source Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For every file in ``src/``, there is exactly one corresponding test file in
``unit_tests/``, named ``test_{src_file_name}.py``, mirroring the directory structure of
``src/``.

.. code-block:: text

    src/
        my_package/
            report_generator.py     →   test/unit_tests/my_package/test_report_generator.py
            string_utils.py         →   test/unit_tests/my_package/test_string_utils.py

Each source file must reach 100% branch and line coverage when its corresponding test
file is run in isolation.

Only Call Public Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests call only functions, classes, and attributes that are part of the module's
public interface — those not prefixed with an underscore.  If a behavior can only be
reached by calling a private function directly, that is a signal to either:

* Make the function public if it represents a real use case, or
* Test it indirectly through the public functions that call it.

Testing private functions by name couples the test to the implementation.  If the
implementation is refactored and the private function is renamed or removed, the test
breaks even though the behavior is preserved.

On Mocks and Patches
~~~~~~~~~~~~~~~~~~~~~

Mocks and patches are a last resort, not a first tool.  The reason is simple:
**mocks encode the current implementation**.  A mock that patches an internal function
call by name will break the moment that call is refactored away, even if the observable
behavior of the module is unchanged.

Use real objects wherever practical.  Set up real data structures, real file system
paths in temporary directories, and real collaborator objects.

Use mocks or patches only when:

* The dependency involves significant external infrastructure that is genuinely impractical
  to set up in a test (e.g., a third-party cloud service, a physical device).
* The dependency is non-deterministic in a way that makes assertions impossible (e.g., the
  current wall-clock time, a random number generator that you cannot seed).
* Setting up the real dependency would take an unreasonably large amount of test code that
  obscures the behavior being tested.

When a mock is justified, mock at the boundary (the external service, the I/O call) and
not in the middle of your own code.  Patching a function defined in the same module being
tested is almost always wrong.

Parameterization
~~~~~~~~~~~~~~~~

Use ``@pytest.mark.parametrize`` liberally to cover the range of valid and invalid inputs
a function accepts.  A single test function with many parameter sets is far more readable
than many nearly-identical test functions.

.. code-block:: python

    @pytest.mark.parametrize(
        ("input_code", "expected_label"),
        [
            ("US", "United States"),
            ("GB", "United Kingdom"),
            ("DE", "Germany"),
            ("JP", "Japan"),
        ],
    )
    def test_country_code_resolves_to_label(input_code: str, expected_label: str) -> None:
        assert resolve_country_label(input_code) == expected_label

Fixtures in unit tests are function-scoped by default.  Each test gets a fresh instance.
Session-scoped fixtures are rarely appropriate in unit tests because unit tests should be
fast enough that sharing state across tests provides no meaningful benefit.

Coverage
~~~~~~~~

100% branch and line coverage is required for every source file, verified by running the
corresponding test file in isolation.  After individual file checks, all unit tests for
the subproject are run together to produce an aggregate report.

Shared Conventions
------------------

conftest.py Organization
~~~~~~~~~~~~~~~~~~~~~~~~~

Fixtures are organized in a hierarchy of ``conftest.py`` files:

.. code-block:: text

    test/
        conftest.py                  ← fixtures shared by all test types
        unit_tests/
            conftest.py              ← fixtures for unit tests only
        feature_tests/
            conftest.py              ← fixtures for feature tests only

Keep fixtures in the most specific ``conftest.py`` that will use them.  A fixture used
only by feature tests does not belong in the root ``conftest.py``.

Fixtures should be composed: a complex fixture should be built from simpler fixtures
rather than doing everything itself.  This makes the dependency chain visible and makes
individual pieces reusable.

Test Resource Directories
~~~~~~~~~~~~~~~~~~~~~~~~~~

When a test needs static input files (JSON payloads, CSV data, expected output
fixtures), place them in a directory named after the test file with ``_resources``
appended:

.. code-block:: text

    test/unit_tests/test_report_generator.py
    test/unit_tests/test_report_generator_resources/
        input_records.json
        expected_output.json

Use the ``test_resource_dir`` fixture (defined in the root ``conftest.py``) to get the
path to this directory automatically.

Checksum Tests for Static Resource Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a module loads static resource files at runtime (YAML tables, embedded data files,
lookup tables), two tests are required to guard against accidental edits and to enforce
that the code stays in sync with the filesystem.

**Pattern:**

Define an enum whose members each pair a resource identifier with its expected SHA256
checksum.  One parametrized test verifies every known resource file against its
checksum.  A second test verifies that the number of enum members matches the number of
files actually present in the resource directory.

.. code-block:: python

    import hashlib
    from enum import Enum
    from pathlib import Path
    from typing import NamedTuple

    import pytest
    from my_package import resource_loader


    def _resource_dir() -> Path:
        return Path(resource_loader.__file__).parent / "resources"


    def _hash_file(name: str) -> str:
        text = (_resource_dir() / name).read_text().replace("\r\n", "\n")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


    class _ResourceChecksum(NamedTuple):
        filename: str
        expected_sha256: str


    class KnownResource(Enum):
        FOO = _ResourceChecksum("foo.yaml", "abc123...")
        BAR = _ResourceChecksum("bar.yaml", "def456...")


    @pytest.mark.parametrize("resource", list(KnownResource), ids=lambda r: r.name)
    def test_resource_file_matches_expected_checksum(resource: KnownResource) -> None:
        """Each known resource file must match its recorded checksum."""
        assert _hash_file(resource.value.filename) == resource.value.expected_sha256


    def test_resource_enum_matches_file_count() -> None:
        """Number of files in the resource directory must match enum member count."""
        files = list(_resource_dir().glob("*.yaml"))
        assert len(files) == len(KnownResource)

**Why two tests:**

* The checksum test catches silent edits to existing files — changing a value inside a
  YAML table will flip the hash and fail immediately.
* The count test catches additions and deletions — adding a new resource file without a
  corresponding enum member (or vice versa) fails immediately, prompting the developer
  to record the new checksum.

The checksum is computed over normalized line endings (``\r\n`` → ``\n``) so that the
test is stable across Windows and Unix checkouts.

Naming Conventions
~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Element
     - Convention
     - Example
   * - Unit test file
     - ``test_{src_file_name}.py``
     - ``test_report_generator.py``
   * - Feature test file
     - ``test_{ticket_id}_{project_name}.py``
     - ``test_42_template_python_project.py``
   * - Test function
     - ``test_{behavior_being_verified}``
     - ``test_empty_input_returns_zero_total``
   * - Fixture
     - Noun or noun phrase describing the thing provided
     - ``generated_report``, ``input_json_file``
   * - Resource directory
     - ``{test_file_stem}_resources/``
     - ``test_report_generator_resources/``

Test functions should be named for the behavior they verify, not for the function they
call.  ``test_empty_input_returns_zero_total`` is good.  ``test_calculate`` is not.

Type Annotations
~~~~~~~~~~~~~~~~~

All test functions and fixtures must have complete type annotations, consistent with the
mypy configuration used for source code.  This makes fixture dependency chains
self-documenting and catches errors in test setup early.
