Tickets
=======

This page provides links to all ticket requirement documents.  Each ticket document contains
the detailed requirements, acceptance criteria, and technical specifications for a feature
or bug fix.  Tickets are stored in the :code:`docs/tickets` directory.

The GitHub issue serves as the single source of truth for the current status of a ticket
(e.g., in progress, ready for review, completed).  The documentation stored here provides
the detailed requirements and acceptance criteria that inform the development work.

Active Tickets
--------------

.. toctree::
   :maxdepth: 1
   :glob:

   tickets/*

.. note::
   When creating a new ticket, the Product Manager should:

   1. Create a GitHub issue with a brief description of the need
   2. Create a branch associated with the GitHub issue
   3. Add a new :code:`.rst` file in the :code:`docs/tickets` directory following the naming
      convention :code:`{full-branch-name}.rst`
   4. Document all requirements and acceptance criteria in the :code:`.rst` file
   5. Move the GitHub issue to "Ready" when requirements are clear and acceptance criteria
      is falsifiable

   The ticket :code:`.rst` file will be automatically included in the list above.
