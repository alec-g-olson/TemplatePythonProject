107: Suffix Docker Image Tags With Ticket ID on Non-Main Branches
==================================================================

Overview
--------
This ticket updates local Docker image tagging so parallel branch work on the same
machine does not collide on shared image names. On ``main``, tags stay unchanged
(``dev``, ``prod``, ``build``). On non-main branches, tags are suffixed with the
branch ticket id (for example ``dev-100``, ``prod-100``, ``build-100``).

Requirements
------------

User Flow
~~~~~~~~~
1. A developer runs project make/docker workflows from ``main``.
2. The workflows build/use the standard unsuffixed tags (for example ``dev``,
   ``prod``, ``build``).
3. A developer runs the same workflows from a non-main ticket branch such as
   ``100-short-description-of-branch``.
4. The workflows build/use ticket-scoped tags by appending ``-100`` to each base tag.
3. A developer runs the same workflows from a non-main ticket branch such as
   ``101``.
4. The workflows build/use ticket-scoped tags by appending ``-101`` to each base tag.

Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~
- Apply this tagging rule consistently anywhere project tooling builds or references
  local project images (including existing base tags such as ``build``, ``dev``, and
  ``prod``).
- Ensure branch-scoped tags prevent cross-branch image reuse on the same machine.
- Keep behavior unchanged for ``main``.

Acceptance Criteria / Feature Tests
-----------------------------------

- A ticket feature test exists for ticket ``107`` and validates a hyphenated ticket
  branch (for example ``100-short-description-of-branch``) resolves to
  ``{base_tag}-100``.
- A ticket feature test exists for ticket ``107`` and validates a ticket-id-only branch
  (for example ``TEST001``) resolves to ``{base_tag}-TEST001``.
- Tests demonstrate that two different ticket branches resolve to different Docker tags
  and therefore do not collide.

Developer Notes
---------------
- We should have function that is called anywhere in the build_support code that
  generates a docker image tag with the correct name, do not rely on keeping it
  consistent across the codebase without a function.
- There are a few places in Makefile where we construct the image tag names. e.g.
  `DOCKER_DEV_IMAGE = $(PROJECT_NAME):dev` We'll need to come up with some logic so we
  can instead do `DOCKER_DEV_IMAGE = $(PROJECT_NAME):dev(TAG_SUFFIX)` where `TAG_SUFFIX`
  is empty when on main.
