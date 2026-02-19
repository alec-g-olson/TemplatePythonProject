100: Add Ticketing System and Make Documentation Generic
========================================================

Overview
--------
This ticket updates the template so project work is tracked through ticket files
and the docs/examples are reusable across domains. It also introduces a concrete,
small reference implementation (calculator) that demonstrates the intended layered
architecture and test strategy for new projects.

Requirements
------------

User Flow
~~~~~~~~~
1. A developer creates or checks out a branch.
2. The user must make a matching ticket file at
   ``docs/tickets/{project_name}/{full-branch-name}.rst`` where the filename exactly
   matches the branch name.  As a reminder, branch names follow the format
   ``{ticket_id}`` or ``{ticket_id}-{short-description}``.

Additional Documentation
~~~~~~~~~~~~~~~~~~~~~~~~
- Update ``docs/source_code_style_guide.rst`` with domain-generic guidance that
  outlines this repositories philosophy towards code organization and style that can
  be followed by both developers and AI agents.
- Update ``docs/testing_style_guide.rst`` with domain-generic guidance that
  outlines this repositories philosophy towards testing and validation that can
  be followed by both developers and AI agents.
- Update ``AGENTS.md`` so agent instructions align with the ticket workflow and
  template-project terminology.
- Add a ``CLAUDE.md`` that references ``AGENTS.md``.
- Add a ``TEMPLATE.rst`` ticket.

Example Code Updates
~~~~~~~~~~~~~~~~~~~~
- Update the calculator source code in
  ``pypi_package/src/template_python_project`` as the concrete example of the
  documented architecture and testing practices.

Acceptance Criteria / Feature Tests
-----------------------------------

User Flow
~~~~~~~~~
- A feature test exists that checks the ticket-file workflow is enforced (e.g. that
  a ticket file at ``docs/tickets/{project_name}/{full-branch-name}.rst`` is required
  or validated where the filename matches the current branch name).

Documentation Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~
- The following docs exist and are updated as specified in the requirements:
  ``docs/source_code_style_guide.rst``, ``docs/testing_style_guide.rst``,
  ``AGENTS.md``, ``CLAUDE.md`` (referencing ``AGENTS.md``), and ``TEMPLATE.rst``.

Example Code Updates
~~~~~~~~~~~~~~~~~~~~
- Feature tests exist that show the calculator example code works as expected and
  demonstrate the documented architecture and testing practices.
