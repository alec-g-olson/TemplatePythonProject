98: Switch Static Typing from mypy to ty
========================================

Overview
--------
This ticket migrates repository static type checks from mypy to ty.
The goal is to keep strict typing enforcement while standardizing on Astral tooling.

Requirements
------------
- Replace mypy-based type checking with ty across build tooling and test coverage.
- Configure ty so all checks are enforced at error level.
- Remove mypy-specific configuration and command wiring from the repo.
- Update feature tests that rely on mypy if needed.
- Determine the maximum number of rules that can be readily enforced on this repo.
- We must use all the default ty rules, and we'd prefer to be able to use all of them.

Acceptance Criteria / Feature Tests
-----------------------------------
- Running :code:`make type_checks` uses ty and succeeds on the repository.
- Running :code:`make type_check_build_support` uses ty and reports failures for
  intentionally invalid type-check fixture files.
- :code:`pyproject.toml` contains ty configuration with all checks set to error, and no
  mypy configuration block remains.
