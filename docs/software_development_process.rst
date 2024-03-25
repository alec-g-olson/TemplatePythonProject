Software Development Process
============================

Below is a centralized, human-readable description of the development process used by
the team that works on this project.  If any changes are made to this document the
appropriate figures in your organization must approve the changes.  When possible the
process described below should be enforced by software.

Software methods of process enforcement include but are not limited to:
 - The CI/CD pipeline in build_support
 - Setting infrastructure permissions and roles using Pulumi
 - Adding required PR reviewers using code ownership configs (or similar)

Updating The Software Development Process
-----------------------------------------

The development process can only be updated as the result of a team retrospective.  The
technical lead and product manager must both agree on any changes to the process.  These
two roles should strongly consider the opinions of the developers when making changes,
and work with them to find process that the entire team can agree on.

A retrospective ticket must be made at the start of each retro.  Meeting minutes/notes
must be captured on this ticket.  If process or process enforcement changes are agreed
to then a branch associated with the retrospective ticket should be made, allowing for
this document to be edited.  If the software changes to enforce new or existing process
are sufficiently small they can be included in this branch alongside the proposed
process changes.  Any additional software changes to enforce process must get their own
tickets and have links to those tickets added to this page in the
`Outstanding Process Enforcement Tickets`_ section.  The branch with process changes
must be merged by a pull request approved by the product manager and technical lead.

The process enforcement tickets must be created and process change pull request must be
merged the same day as the retrospective to keep this document accurate.  If writing
these enforcement tickets or changes to process will take too long the technical lead
and product manager (in consultation with the team) must reduce the scope of the
changes, and allow the excess changes to be addressed in a future retrospective.

Outstanding Process Enforcement Tickets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any elements of process that can be enforced by code should be implemented as soon as
possible and take priority over other tickets.  If other tickets are business critical
and require immediate completion then process changes should be delayed until those
critical tickets are completed.

Once a new process is agreed on the reality is that sometimes it can take some time
to complete the new enforcement tickets.  We will change this document to reflect the
new process as soon as it is agreed to, but as a warning to software team stakeholders
attempting to follow the process we will record incomplete process enforcement here.

Tickets:
 - None!


Roles and Responsibilities
--------------------------

Below are the roles and responsibilities of the software development team.  Anyone who
has one of these roles is considered to be a member of the software development team.
As a general rule multiple roles should not be assigned to the same person, but on
particularly small teams this is sometimes unavoidable.

Product Manager
~~~~~~~~~~~~~~~
    - Alec

Responsibilities
^^^^^^^^^^^^^^^^

The product manager is responsible for discovering business needs and gathering the
requirements for products and features that will address those business needs.  This
includes but is not limited to communicating internally with commercial, sales, and
product stakeholders, gathering feedback directly from customers, or making assessments
based on the existing business landscape.

Technical Lead
~~~~~~~~~~~~~~
    - Alec

Responsibilities
^^^^^^^^^^^^^^^^

The the technical lead has all of the responsibilities of the developers, with the
added responsibility of being the final decision maker for technical decisions.  This
includes but is not limited to technical processes, product architecture, and
technologies selected for development.  Although the technical lead has final say, they
should actively seek out the insights that the other developers can provide and rarely
exercise their authority to make unilateral decisions.

Because the technical lead has all the responsibilities of developers whenever
developers are mentioned in this document it should be assumed that the technical lead
is included in that group of people unless explicitly stated otherwise.

Developers
~~~~~~~~~~
    - None

Responsibilities
^^^^^^^^^^^^^^^^

Developers are responsible for creating technical requirements for features, estimating
the complexity of those features, and doing the work required to deliver features that
the product manager believes will provide appropriate business value given the
developers estimates.


Software Development Lifecycle
------------------------------

Definitions
~~~~~~~~~~~
.. list-table::
   :widths: auto
   :header-rows: 1

   * - Term
     - Definition
   * - Ticket
     - A document that exists to track work required to deliver features.  Can have
       sub-tickets and parent tickets.
   * - Backlog
     - The collection of all tickets that have not been approved for development.
   * - Feature
     - A proposed capability of the software that is believed will provide business
       value.
   * - Bug
     - An issue discovered in the implementation of a previously completed feature. (Not
       a design oversight of a feature)


Adding Features to the Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Feature tickets can be only added to the backlog by the product manager.  Feature
tickets can stay in the backlog in a partially completed state as the product manager
gathers requirements and assesses the business value of the ticket.

The product manager is the only person who can declare a feature's requirements to be
ready, and is also the only person who can assign a business value to a ticket.

Adding Bugs to the Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~

Bugs can be submitted by anyone but must have clear instructions for reproduction.  If
a developer cannot reproduce the bug the developer should go to the individual who
submitted the bug and work with them to determine the steps for reproduction.

The acceptance criteria of a should always be that the broken feature works as
previously described.  This can only be changed in consultation with the product
manager.

Bugs do not get a complexity score.  This is because they represent missed complexity
in past estimates of features.  So the team's velocity should be punished for going back
to do work that they already took credit for.

Scoring and Scoping Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the product manager has completed gathering requirements and accessing the business
value of a feature it is ready to be scored and scoped by the developers.  The
developers will breaking down the feature into sub-tickets as they see fit and then
score them.  When breaking down features the sub-tickets must have an acceptance
criteria and a score.  This acceptance criteria should be written in a technically
agnostic way that emphasizes the useful nature of the work.   For example, instead of
"A column named 'xxx' is added to table 'yyy' in our database." write the acceptance
criteria as "A developer can store and access a value for property 'xxx' of object 'yyy'
using our API."

If a feature requires minimal technical work to complete it is possible that a new
ticket does not need to be created.  In this case the feature's requirements can be
considered it's acceptance criteria and only an complexity score should be added to it.

If there are many sub-tickets it's likely that some of them will be dependent on
each other.  Tickets should link to each other in a way that makes it clear to the
members of the team what tickets are blocked and what work needs to be done to unblock
them.

Estimating Complexity
^^^^^^^^^^^^^^^^^^^^^
In order for the product manager to make informed decisions about the business
value/cost trade-off of features the developers must provide estimates.  However,
estimates are inherently fuzzy and there is no need to be more precise than is feasible.

To estimate the complexity of a ticket the developers will first discuss the ticket to
get a cursory understanding of the ticket, this should take no more than 5 minutes and
should generally be 1-2 minutes.  Then each developer can vote (without the knowledge of
other developers votes) on the complexity they expect the ticket will take.  This is
done by submitting a fibonacci number (1, 2, 3, 5, 8, 13, etc...).  Once all voting members have
submitted their vote they check to see if they all agree.

Complexity Values
'''''''''''''''''
These values should start as days of work, but eventually become relative to past
tickets.  This is so that the team can measure its velocity in complexity navigated.
Hopefully as the team builds better tooling and establishes better processes its
velocity can increase.  If the team sticks to complexity being measured in days of work
then the velocity cannot increase.

Prioritizing Ready Tickets
~~~~~~~~~~~~~~~~~~~~~~~~~~

When tickets belonging to a feature with business value have both an acceptance criteria
and a complexity assigned they can be considered ready.  The product manager is responsible
for ordering the ready tickets by priority for the developers.  Generally tickets
belonging to the same feature will be grouped together, but it can be possible for
the team to be working on multiple features at once if the higher priority feature has
tickets that are blocked.

Backlog Grooming
~~~~~~~~~~~~~~~~

At regular intervals the software team will meet to review the backlog and ensure that
the state of the tickets is appropriate.

This includes:

 - Flagging features with complete requirements to be scored by the developers
 - Flagging stale features for removal from the backlog
 - Flagging missing or ambiguous requirements of in-progress features
 - Collaborating on feature prioritization (product manager is final decision maker)

Completing Tickets
~~~~~~~~~~~~~~~~~~

The work associated with a ticket must be reviewed by another developer, as well as any
required stakeholders as defined by the software development process.

If the ticket being completed is a feature the product manager must review the new
behavior before it can be closed.


Continuous Integration and Deployment Process
---------------------------------------------

In order for a pull request to be completed our automated test suite must first
successfully complete, and when a pull request is merged our deployment pipeline runs
automatically.

Ensuring a Consistent Testing and Deployment Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Between this project's Makefile, Dockerfile, and :doc:`build_support` we have gone
to great lengths to make sure that the build, testing, and deployment environments are
the same across any machine.

The Makefile is responsible for gathering variables from the machine (such as path to
the project and user information), running docker prune commands that can't be run from
a docker image, building the :code:`build` docker image, and running build commands
using a :code:`build` container from that image.  All other build pipeline logic is
contained in the :doc:`build_support`.

The Dockerfile in this project is responsible for maintaining the environments we will
use for building, testing, and deploying artifacts.  In the future there might be a
docker image that we use as an artifact, but that is not the case today.

The :doc:`build_support` is used for all the pipeline logic.  When the Makefile executes
either the :code:`execute_build_steps.py` or :code:`report_build_var.py` scripts a DAG
of tasks will be built and executed in the :code:`build` docker image.  Some of these
tasks execute simple tasks such as parsing the pyproject.toml file for the project's
current version number, executing a command like :code:`git fetch`, or making simple
web requests.  However any moderately complex task or one that involves packages not in
the :code:`build` container should be run in another docker container.  The
:code:`build` container has been setup to make Docker out of Docker (DooD) calls where
a command can be sent to the local machine's docker daemon and executed outside of the
:code:`build` container in another container.  The docker container that is chosen to
execute the commands is coded into the :doc:`build_support`'s code.

This system should allow for the build, testing, and deployment of our project to be
done in consistent environments across all \*nix based platforms.

Automated Testing and Style Enforcement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below is a description of the tests we run automatically in order for a pull request to
be allowed to merge.

Check if Project Version is Valid
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step in pushing artifacts during our deployment process is to tag the current
commit with the projects version (located in the :code:`pyproject.toml` file).  Because
of this we enforce the following checks on the project's version.

- There are no existing tags in our git repo that match the project's version
- If we are deploying from the :code:`main` branch we ensure the version follows the
  standard `SemVer <https://semver.org>`_ format. :code:`MAJOR.MINOR.PATCH`
- If we are deploying from any other branch we ensure the version follows our standard
  for dev versions. :code:`MAJOR.MINOR.PATCH-dev.ATTEMPT`

Major, Minor, Patch, and Attempt should all be integer numbers.

Check the Structure of the README.md
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We check that the :code:`README.md` of this project has exactly the headers we expect,
and that the sections for those headers have some contents.

When running tests on any branch other than :code:`main` we test to make sure that all
URLs used in hyperlinks point to a valid website.

Check the Contents of "docs" RST Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We have some tests for a few of the :code:`docs` files to ensure that we don't forget to
update them when required to.

subprojects.rst
'''''''''''''''

We check to make sure that each subproject has a section in this file, and that the ones
with python source files have a link to the sphinx generated documentation of their
sources.

subproject_code_docs.rst
''''''''''''''''''''''''

We check to make sure there is a link to the sphinx generated documentation of every
subproject with source code.

Check Hyperlinks are Valid
''''''''''''''''''''''''''

As long as we are not testing a commit on :code:`main` we check to make sure that all
hyperlinks in the :code:`.rst` files are valid.  We don't check if we are on main,
because we want to be able to rebuild an old version of our pipeline even if a
referenced website has changed URLs since it was first built.

General Python Package Validation Strategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a general validation strategy that the following python packages go through:
 - :doc:`build_support`
 - :doc:`pulumi`
 - :doc:`template_python_project`
 - :code:`process_and_style_enforcement`

Each package generates reports during validation that are placed in
:code:`build/{package_name}/reports`.

For some packages it is inappropriate or incoherent to execute some steps of the
validation process.  Those packages will be explicitly called out when describing the
steps of the validation process.

Ruff
''''
All python files are formatted and linted using the
`Ruff <https://docs.astral.sh/ruff/>`_ tool.  The tool's version and settings are
controlled in :code:`pyproject.toml`.  When we change versions of this tool we set it up
so that all stable rules are run, and unstable rules are skipped.

When running on test code we also turn off pydocstyle (D) and flake8-boolean-trap (FBT)
rules, because they are onerous to enforce and provide very little benefit in test code.

Testing Source Code
'''''''''''''''''''
We require 100% code coverage and all tests to pass.  Test reports are generated and put
into the appropriate report folder.


The :code:`process_and_style_enforcement` package in this project consists entirely of
test code that is run to enforce our development practices.  There is no source code to
test.


MyPy Type Enforcement Tests
'''''''''''''''''''''''''''

We run :code:`mypy` on every package to ensure that typing in enforced.

Bandit Security Tests
'''''''''''''''''''''''''''

We run :code:`bandit` on the source folder of each package to ensure there are no
unknown security threats in our code.  Low risk threats can be specifically disabled
using comments if both the exact threat rule is listed and an explanation is given
about why we don't believe this threat is applicable to our code.

Reports for each package are generated and put into the appropriate report folder.

The :code:`process_and_style_enforcement` package has no source code to test.

Complete Docstring Tests
''''''''''''''''''''''''
Our docstrings get parsed by :code:`sphinx` and turned into web pages, and so we have
added additional docstring enforcement tests not covered by Ruff's pydocstyle (D) rules.

For all packages with a src folder we enforce the following checks for each python
element's docstring:

Packages
........

  * A :code:`SubPackages` section exists where each subpackage in the package is given a
    description, if there are any subpackages.
  * A :code:`Modules` section exists where each module in the package is given a
    description, if there are any modules.

Modules
.......

  * A :code:`Attributes` section exists where each non-function and non-class element of
    the module is described, if there are any it the module.

Functions and Methods
.....................

  * An :code:`Args` section exists where the function or methods arguments are given a
    description.
  * Either a :code:`Returns` or :code:`Yields` section exists where the result of the
    function or method is described.

The :code:`process_and_style_enforcement` package has no source code and is not subject
to these standards.


Deployment Process
~~~~~~~~~~~~~~~~~~

Deployment process to be described when we figure out how we will push artifacts.

Tagging Commits with the Project Version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before we push any other artifacts we tag the current commit with our project version.
This ensures that if any artifacts experience issues when being used we can figure out
exactly what code was used to create them.

When tagging commits we first check to see if there are any uncommitted changes in our
working environment.  These changes would have been used when testing, so we commit them
with an automatically generated commit message before tagging the commit.  This should
only be relevant for DEV versions, because :code:`main` can only be updated by pull
requests.
