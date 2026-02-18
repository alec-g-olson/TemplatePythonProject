"""Calculation service with layered architecture.

This package demonstrates the three-layer architecture pattern:

- **API Layer** (api.py): Versioned request/response models and public
  service function. This is the boundary with external systems.
- **Domain Engine** (calculator.py): Pure business logic for arithmetic
  operations. Accepts domain dataclasses, returns domain dataclasses.
- **Data Models** (data_models.py): Domain types (dataclasses, enums)
  for internal communication.
- **CLI Entrypoint** (main.py): Thin wrapper for command-line invocation.
  Reads JSON, calls API, writes JSON.

Modules:
    | api: Versioned models and public service function.
    | calculator: Domain engine with pure calculation logic.
    | data_models: Domain types and enums.
    | main: CLI entrypoint.
"""
