100: Add Ticketing System and Make Documentation Generic
=========================================================

**Description**

This ticket modernizes the project template by:

1. **Establishing a ticketing system** — Creates the infrastructure for tracking work via GitHub tickets stored in ``docs/tickets/`` with a standardized RST format and automated validation.

2. **Making documentation generic** — Replaces all domain-specific (assembly design / biology) examples throughout the style guides with universally applicable examples that work for any project type.

3. **Providing a real-world example** — Implements a calculator application that demonstrates the layered architecture pattern across the codebase:
   - **Domain engine** (pure business logic as dataclasses)
   - **API layer** (versioned request/response models, service functions)
   - **CLI entrypoint** (thin wrapper for I/O)
   - **Complete test suite** (unit tests with 100% coverage)

4. **Enforcing ticketing discipline** — Adds automated style checks to ensure that every feature branch has a corresponding ticket file, preventing untracked work.

**Acceptance Criteria**

- [ ] ``docs/tickets/{ticket-id}-{description}.rst`` exists and contains ticket requirements
- [ ] All examples in ``docs/source_code_style_guide.rst`` are domain-generic (no DNA, codons, amino acids, assembly design references)
- [ ] All examples in ``docs/testing_style_guide.rst`` are domain-generic (no FASTA, genetic code, translation references)
- [ ] ``AGENTS.md`` references are updated to use template project names instead of assembly-design names
- [ ] Calculator example implements the full layered architecture:
  - [ ] Domain engine in ``calculators/calculator.py`` (pure function, dataclasses)
  - [ ] Domain data models in ``calculators/data_models.py`` (``CalculationType``, ``CalculationRequest``, ``CalculationResult``)
  - [ ] API layer in ``api/api.py`` (service function with translation logic)
  - [ ] Versioned models in ``api/data_models.py`` (``CalculatorInput``, ``CalculatorOutput`` using ``VersionedModel``)
  - [ ] CLI in ``main.py`` (thin I/O wrapper)
- [ ] Full test coverage for all new and refactored code:
  - [ ] ``test/unit_tests/calculators/test_data_models.py`` (domain types)
  - [ ] ``test/unit_tests/calculators/test_calculator.py`` (domain engine)
  - [ ] ``test/unit_tests/api/test_data_models.py`` (versioned models with version validation)
  - [ ] ``test/unit_tests/api/test_api.py`` (API service function)
  - [ ] ``test/unit_tests/test_main.py`` (CLI entrypoint)
- [ ] Automated test enforces that every feature branch has a ticket file in ``docs/tickets/``
- [ ] All tests pass: ``make test`` succeeds with 100% coverage
- [ ] Documentation is consistent with the example implementation

**Implementation Notes**

**Generic Examples Replaced**

The style guides previously used biology-specific domain examples (DNA sequences, codons, amino acids, genetic code). These have been replaced with generic examples appropriate for any project:

- **Old examples:** amino acid conversion, codon tables, species selection, FASTA files, genetic code
- **New examples:** currency conversion, pricing configuration, country codes, JSON payloads, rate tables

This makes the template usable as a starting point for projects in any domain — financial systems, e-commerce, data analysis, web services, etc.

**Layered Architecture Pattern**

The calculator implementation demonstrates the three-layer pattern recommended in the style guide:

1. **Domain** (``calculators/calculator.py``): Pure function that accepts dataclasses, performs computation, returns dataclasses. No I/O, no external knowledge of versioning or validation.

2. **API** (``api/api.py`` + ``api/data_models.py``): Translation layer that accepts versioned request models, unpacks them into domain dataclasses, calls the domain function, and wraps the result in a versioned response model. The domain and API are completely decoupled.

3. **CLI** (``main.py``): Thin I/O wrapper that parses command-line arguments, reads JSON from disk, calls the API function, and writes JSON to disk. Contains no business logic.

**Dependency Flow**

```
CLI (main.py)
    ↓
API (api/api.py) ← Versioned Models (api/data_models.py)
    ↓
Domain (calculators/calculator.py) ← Domain Types (calculators/data_models.py)
```

Each layer depends only on layers below it. The domain has no knowledge of versioning, HTTP, or any infrastructure concern.

**Testing Strategy**

- **Unit tests** mirror the source structure and test each layer independently
- **Domain tests** verify pure computation logic with dataclasses
- **API tests** verify versioned model validation, serialization, and service function behavior
- **CLI tests** verify argument parsing and I/O operations
- All tests use real objects; no mocks except where external infrastructure is involved

**Automated Ticket Validation**

A new style enforcement test verifies:
- Every feature branch (branches not matching ``main``, ``master``, or ``develop``) has a corresponding ticket file
- The ticket file is named according to the pattern: ``docs/tickets/{ticket-id}-{slug}.rst``
- The ticket file exists and is non-empty

This prevents work from being done without creating a ticket, ensuring traceability and planning discipline.

**Testing**

Feature test coverage:
- Calculator CLI accepts JSON input, produces correct JSON output
- All four arithmetic operations work correctly
- Division by zero is handled appropriately
- Version migration works as expected

Unit test coverage:
- 100% line and branch coverage for all new source files
- All test files verified to run in isolation

**Resources**

- **Style Guide:** ``docs/source_code_style_guide.rst`` — architecture, naming, functions, data models
- **Testing Guide:** ``docs/testing_style_guide.rst`` — unit vs. feature tests, parametrization, fixtures
- **Example Implementation:** ``pypi_package/src/template_python_project/`` — calculator domain and API
- **Test Suite:** ``pypi_package/test/unit_tests/`` — comprehensive test coverage
