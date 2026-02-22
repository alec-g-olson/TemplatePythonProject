Ticket Template
===============

Overview
--------
In 1–3 sentences:
- What user-facing change are we making?
- Why does it matter (pain solved / value added)?

Requirements
------------
Keep these in user / behavior terms. Avoid implementation details
Not every subcategory is needed, for example tickets for CI/CD enhancements will
probably have a User Flow but not Input/Output Spec sections.

User Flow
~~~~~~~~~
- What is the enforced user experience.

Additional Documentation
~~~~~~~~~~~~~~~~~~~~~~~~
- documentation requirements other than standard code docstrings

Input Spec
~~~~~~~~~~
- What triggers this? (user action, request, event)
- Inputs/constraints (formats, limits, assumptions)
- Example input(s) (optional):

Output Spec
~~~~~~~~~~~
- What should the user/system observe?
- Response shape / visible result (messages, UI changes, artifacts)
- Example output(s) (optional):

Functional Requirements
~~~~~~~~~~~~~~~~~~~~~~~
Keep these in user / behavior terms. Avoid implementation details.
Only include must have requirements, our goal is to keep these tickets doable
within a day, that takes discipline in the requirements.

Acceptance Criteria / Feature Tests
-----------------------------------
Provide a list of end-user facing acceptance tests in plain language that can be
implemented to validate the requirements given.
If possible provide concrete example cases.

Developer Notes
---------------
Anything useful for completing the work quickly:
- Links, screenshots, prior tickets
- Edge cases to watch
- Known tradeoffs

If providing implementation details, keep these notes extremely high level so that
an agent reading them in the future isn't bound to an architecture that only made
sense when you wrote this ticket.