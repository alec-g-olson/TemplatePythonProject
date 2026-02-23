97: Switch Container Tooling From Poetry to UV
==============================================

Overview
--------
This ticket migrates container-level dependency and build command usage from Poetry to
uv. It also enforces that the Docker development container exposes uv while Poetry is
not available as a command.

Requirements
------------

User Flow
~~~~~~~~~
1. A developer builds or uses the existing Docker development image.
2. Running ``uv`` in that container succeeds.
3. All future development work in this project will use ``uv`` not ``poetry``.
4. Any references to `poetry` are removed from the dockerfile and the pyproject.toml.
5. poetry.lock is removed and replaced with a uv lock file

Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~
- Docker image setup must use uv commands in place of poetry commands.
- uv environment dependencies must be declared in ``pyproject.toml`` and consumed from
  there during Docker image setup.
- The PyPI package build task must invoke uv instead of poetry.
- The development container must have ``uv`` available and ``poetry`` unavailable.

Acceptance Criteria / Feature Tests
-----------------------------------
- A ticket feature test exists for ticket ``97`` that executes both commands in the
  development container and verifies:
  - ``poetry --version`` fails with a command-not-found style error.
  - ``uv --version`` succeeds.
