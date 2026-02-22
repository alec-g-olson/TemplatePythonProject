# Agent Guide

This file orients an AI agent working in this repository.  Read it fully before starting
any task.

---

## 1. Finding the Ticket for the Current Work

This repo uses GitHub only to track the status and approvals of work done.
The description of the work is in the [tickets](docs/tickets) directory.

**One ticket = one branch.** Each ticket has exactly one associated GitHub branch, created
when the ticket is opened. The branch name starts with the ticket ID and may include a
hyphenated description.

1. Get the current branch name:
   ```bash
   git branch --show-current
   ```

2. Open or create the corresponding requirements file:
   ```
   docs/tickets/{project_name}/{full-branch-name}.rst
   ```
   For example: `docs/tickets/template_python_project/42-add-csv-export.rst`

That file contains the requirements and acceptance criteria for the work.  Read it before
writing any code.

**Multiple branches for the same ticket should not be created.** If a ticket is prematurely
merged before all work is complete, a new bug ticket must be created to finish the work,
with its own branch and documentation.

When creating a new ticket, use the [ticket template](docs/tickets/TEMPLATE.rst) as a starting point.

---

## 2. Useful Developer Commands

All standard commands are in [developer_tooling.rst](docs/developer_tooling.rst).
Read that file for the full list.  The most important ones for day-to-day work are:

| Command | What it does |
|---|---|
| `make test` | Runs the full pipeline: unit tests, feature tests, style, type checks, security. Run this before marking work complete. |
| `make format` | Formats all Python files with Ruff. Run this before committing. |
| `make lint` | Lints with safe fixes. |
| `make type_checks` | Runs mypy across all packages. |
| `make test_pypi` | Runs unit and feature tests for `pypi_package` only. Faster than `make test`. |
| `make test_build_support` | Runs unit and feature tests for `build_support` only. |

Always run `make test` before considering any ticket complete.

---

## 3. Running Commands in Docker

All build, test, and development work runs inside Docker containers.  The `make` commands
handle the Docker plumbing automatically.

### The Three Environments

**`build` (`template-python-project:build`)**

The CI/CD orchestration container.  This is what every `make` command uses internally.
It installs only the `build` dependency group and puts only `build_support/src` on
`PYTHONPATH`.  You never need to target this image directly; the Makefile does it for
you.

**`dev` (`template-python-project:dev`)**

The development container.  It installs all dependency groups (`dev`, `build`, `pulumi`)
and puts every `src` and `test` folder from every subproject on `PYTHONPATH`.  This is
the container to use whenever you need to run a Python command manually — a one-off
script, a REPL, a specific test file.

**`prod` (`template-python-project:prod`)**

The production container.  It installs only the main (non-optional) dependencies and
puts only `pypi_package/src` on `PYTHONPATH`.  It represents exactly what ships.

### When `make` is overkill

If you need to run a specific command, use the dev image.

For example, if you've run `make test` and got an error, the command that resulted in
that error will have been displayed by the `make test` output right before the error.
You can use that docker command directly to test if you have resolved the error before
running `make test` again.

The pattern mirrors what the Makefile does internally:

```bash
docker run --rm \
  --network host \
  --workdir=/usr/dev \
  -v "$(pwd):/usr/dev" \
  -e PYTHONPATH=/usr/dev/pypi_package/src:/usr/dev/build_support/src:/usr/dev/infra/src:/usr/dev/pypi_package/test:/usr/dev/build_support/test \
  template-python-project:dev \
  <command>
```

Key points:
- `--workdir=/usr/dev` — the project root inside the container is always `/usr/dev`.
- `-v "$(pwd):/usr/dev"` — mounts the project from your current directory.
- `-e PYTHONPATH=...` — the dev image needs all `src` and `test` folders on the path.
- The image must already be built (`make setup_dev_env` if it is not).

For a `prod`-equivalent run (only the pypi package, no test or build code):

```bash
docker run --rm \
  --workdir=/usr/dev \
  -v "$(pwd):/usr/dev" \
  -e PYTHONPATH=/usr/dev/pypi_package/src \
  template-python-project:prod \
  python pypi_package/src/template_python_project/main.py --input in.json --output out.json
```

### Dependency Changes

Never run `poetry install` or `poetry lock` outside a container.
`docker run ... <command>` is sufficient.

---

## 4. Designing Source Code

Before writing any code, read `docs/source_code_style_guide.rst`.  The key principles
that most frequently affect day-to-day decisions are summarized here.

**The layer rule**: dependencies flow downward only.
```
CLI / Entrypoints   →  parses args, reads/writes files, calls the API layer
API layer           →  validates versioned input, translates to plain values/dataclasses,
                       calls ONE top-level domain function, wraps result in versioned output
Domain packages     →  business logic and algorithms; communicate via dataclasses
Utilities           →  shared types, type aliases, pure helpers,
Persistence         →  resource file I/O, database access, can use versioned models
```

**`VersionedModel` is only for the API boundary.**  Versioned Pydantic models exist to
handle evolving serialized formats.  They are used to validate incoming JSON and to
produce outgoing JSON.  Once inputs are validated, the API and persistence layer
restructure the data into dataclasses accepted by the domain functions.  Domain and
utility functions do not use versioned models.

**Dataclasses are the internal currency.**  Pass structured concepts between functions
using `@dataclass(frozen=True)`.  One package may import and construct another package's
dataclass in order to call that package's function — this is the correct collaboration
pattern.

**Shared domain types live in utilities.**  `EmailAddress`, `CurrencyCode`, and
similar fundamental types are defined once in a utility package and imported everywhere.
They are never redefined per subpackage.

**Prefer pure functions.**  Business logic should depend only on its arguments.  Use
classes only when state genuinely needs to persist across calls.

**Enums over strings and booleans.**  Fixed sets of values get an enum.

**Git metadata convention.**  When build/process code needs the current ticket id,
use `GitInfo.ticket_id` as the only source of truth. Do not add new branch-name parsing
helpers that duplicate this logic. If loading from disk, parse `git_info.yaml` via
`GitInfo.from_yaml(...)`; if deriving from branch text, construct/validate through
`GitInfo` so ticket-id behavior stays centralized.

Read the full guide for docstring requirements, naming conventions, CLI entrypoint
structure, and the rules around suppression comments.

---

## 5. Designing and Writing Tests

Before writing any tests, read [testing_style_guide.rst](docs/testing_style_guide.rst).
The most important points:

**Two kinds of tests:**

- **Unit tests** (`test/unit_tests/`) — one test file per source file, named
  `test_{src_file_name}.py`, mirroring the `src/` directory structure.  Test the
  complete use cases of the module through its public interface only.  Avoid mocks;
  use real objects.  Each source file must reach 100% coverage when its corresponding
  test file runs in isolation.

- **Feature tests** (`test/feature_tests/`) — one file per ticket, named
  `test_{ticket_id}_{project_name}.py`.  Test the software the way a user experiences
  it: currently by invoking the CLI as a subprocess.  Use session-scoped fixtures for
  anything expensive to set up.

**Mocks are a last resort.**  Mocks encode the current implementation; when the
implementation changes the mock breaks even if the behavior is preserved.  Use a mock
only when a real dependency involves external infrastructure that is genuinely
impractical to set up in a test.

**The feature test file for the current ticket is required.**  The pipeline will not
allow a merge without a file at:
```
test/feature_tests/test_{ticket_id}_{project_name}.py
```
containing at least one `def test_` function.  Write this file even if the ticket is
purely structural (see the style guide for the rare exception procedure).

**100% coverage is required** for both unit and feature test files.  Every line in a
test file must execute during a test run.
