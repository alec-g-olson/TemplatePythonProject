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

Retrospective
~~~~~~~~~~~~~

All changes to the team’s process must be unanimously approved by the participants of a
retrospective meeting, including the Technical Lead and Project Manager. If a change
later proves ineffective or unnecessarily burdensome, it may be reversed in a future
retrospective.

Retrospectives may be held at any time and are not required to follow a fixed schedule.
However, the must be minimally attended by the Product Manager, the Technical Lead, and
at least half of the Developers.

Retrospective Process
^^^^^^^^^^^^^^^^^^^^^

At the beginning of each retrospective, create a new GitHub issue and a branch.  Then make
a new retrospective page in the :code:`docs/retros` directory following the naming
convention :code:`YYYY-MM-DD-retrospective.rst`.  All meeting notes and action items must
go on this page inside the documentation for this project.  Once it is done a PR will be
opened for the branch and the attendees of the retro will approve its merge to main.

All retrospectives are linked from the :doc:`retrospectives` page.

Start by linking the previous retrospective page and reviewing any outstanding action
items. Then discuss new pain points or process insights that have arisen since the last
retrospective. (what went well, what went poorly, what should we start doing, what
should we stop doing) All action items require unanimous approval from retrospective
participants. Once approved, categorize each action item as either Immediate or Future.

**Immediate Action Items**
These are process changes and related enforcement updates that can reasonably be
implemented, reviewed, and merged into :code:`main` by the end of the day. Following
the standard development workflow.

**Future Action Items**
These are items that cannot reasonably be completed within that timeframe.

After categorization, implement all Immediate action items on this branch.

Each Future action item must be converted into its own ticket and handled according
to the process defined in the `Outstanding Process Enforcement Tickets`_ section.

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

The technical lead has all of the responsibilities of the developers, with the
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
     - A GitHub issue that tracks the status of work.  Detailed requirements and
       acceptance criteria are documented in corresponding :code:`.rst` files in the
       :code:`docs/tickets` directory.  Can have sub-tickets and parent tickets.
   * - Backlog
     - The collection of all GitHub issues that have not been approved for development.
   * - Feature
     - A proposed capability of the software that is believed will provide business
       value.
   * - Bug
     - An issue discovered in the implementation of a previously completed feature. (Not
       a design oversight of a feature)


Adding Features to the Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Feature tickets can only be added to the backlog by the Product Manager.  The process for
creating a new feature ticket is:

1. The Product Manager creates a GitHub issue with a brief description of the need
2. The Product Manager creates a branch from the GitHub issue (GitHub will automatically
   name the branch as :code:`{ticket_id}-{short-description}`)
3. The Product Manager creates a corresponding :code:`.rst` file in the :code:`docs/tickets`
   directory named :code:`{ticket_id}-{short-description}.rst`, using the
   :doc:`ticket template <tickets/TEMPLATE>` as a starting point
4. The Product Manager documents all requirements and acceptance criteria in the
   :code:`.rst` file
5. When the developers agree that requirements are complete and clear, and the
   acceptance criteria is falsifiable, the Product Manager may move the GitHub issue to
   "Ready" status

Feature tickets can remain in the backlog in a partially completed state as the Product
Manager gathers requirements and assesses the business value of the ticket.  All
requirements and acceptance criteria should be documented in the ticket's :code:`.rst`
file in the :code:`docs/tickets` directory.

The Product Manager is also the only person who can assign a business value to a
ticket, or move the ticket to "Ready" (given developer approval).

All tickets are linked from the :doc:`tickets` page.

Adding Bugs to the Backlog
~~~~~~~~~~~~~~~~~~~~~~~~~~

Bugs can be submitted by anyone by creating a GitHub issue.  The bug report must have
clear instructions for reproduction.  If a developer cannot reproduce the bug, the
developer should work with the individual who submitted the bug to determine the steps
for reproduction.

The acceptance criteria of a bug should always be that the broken feature works as
previously described.  This can only be changed in consultation with the Product Manager.

Bugs do not get a complexity score.  This is because they represent missed complexity
in past estimates of features.  So the team's velocity should be punished for going
back to do work that they already took credit for.

Scoring and Scoping Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the Product Manager has completed gathering requirements and assessing the business
value of a feature (documented in the ticket's :code:`.rst` file in :code:`docs/tickets`
and marked the GitHub issue as "Ready"), it is ready to be scored and scoped by the
developers.  The developers will review the requirements and acceptance criteria
documented in the ticket's :code:`.rst` file.

The developers may break down the feature into sub-tickets as they see fit and then score
them.  When breaking down features, sub-tickets should be created as GitHub issues and
linked to the parent ticket.  Each sub-ticket must have its own :code:`.rst` file in
:code:`docs/tickets` with acceptance criteria and a complexity score, using the
:doc:`ticket template <tickets/TEMPLATE>` as a starting point.  This acceptance
criteria should be written in a technically agnostic way that emphasizes the useful nature
of the work.  For example, instead of "A column named 'xxx' is added to table 'yyy' in our
database," write the acceptance criteria as "A developer can store and access a value for
property 'xxx' of object 'yyy' using our API."

If a feature requires minimal technical work to complete, it is possible that sub-tickets
do not need to be created.  In this case, the feature's requirements (as documented in its
:code:`.rst` file) can be considered its acceptance criteria and only a complexity score
needs to be added to the GitHub issue.

If there are many sub-tickets, it's likely that some of them will be dependent on each
other.  Tickets should be linked in GitHub in a way that makes it clear to the members
of the team what tickets are blocked and what work needs to be done to unblock them.

Estimating Complexity
^^^^^^^^^^^^^^^^^^^^^
In order for the product manager to make informed decisions about the business
value/cost trade-off of features the developers must provide estimates.  However,
estimates are inherently fuzzy and there is no need to be more precise than is feasible.

To estimate the complexity of a ticket the developers will first discuss the ticket to
get a cursory understanding of the ticket, this should take no more than 5 minutes and
should generally be 1-2 minutes.  Then each developer can vote (without the knowledge of
other developers votes) on the complexity they expect the ticket will take.  This is
done by submitting a fibonacci number (1, 2, 3, 5, 8, 13, etc...).  Once all voting
members have submitted their vote they check to see if they all agree.

Complexity Values
'''''''''''''''''
These values should start as days of work, but eventually become relative to past
tickets.  This is so that the team can measure its velocity in complexity navigated.
Hopefully as the team builds better tooling and establishes better processes its
velocity can increase.  If the team sticks to complexity being measured in days of
work then the velocity cannot increase.

Prioritizing Ready Tickets
~~~~~~~~~~~~~~~~~~~~~~~~~~

When tickets belonging to a feature with business value have both an acceptance criteria
(documented in :code:`docs/tickets`) and a complexity score assigned (recorded in the
GitHub issue), they can be considered ready.  The Product Manager is responsible for
ordering the ready tickets by priority for the developers in GitHub.  Generally, tickets
belonging to the same feature will be grouped together, but it is possible for the team
to be working on multiple features at once if the higher priority feature has tickets
that are blocked.

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

Developers will work on the same branch that was created by the Product Manager when the
ticket was first created.  This branch will contain both the ticket's requirements
documentation (in :code:`docs/tickets`) and all implementation work.  When the work is
complete, a single pull request will be opened to merge all changes (documentation and
implementation) into the main branch at once.

For any given piece of work, developers have freedom to complete their work in any way
they see fit as long as they follow our `Branching`_ and `Pull Request`_ strategies.

Branching
^^^^^^^^^

**One ticket = one branch.** Branches are created by the Product Manager when a ticket is
first created in GitHub. Branch names must start with the ticket ID followed by a hyphen
and a short description of the work, e.g., :code:`{ticket_id}-{description}`.  This format
matches the default when you create a branch from a GitHub issue.  Our pipeline extracts
the ticket ID from the branch name for checks such as requiring a corresponding feature
test file.

The same branch is used throughout the ticket lifecycle: first by the Product Manager to
document requirements in :code:`docs/tickets`, and then by developers to implement the
feature or fix.  All changes are merged together in a single pull request when the work
is complete.

If a ticket is prematurely merged to main before all acceptance criteria are met, a new
bug ticket must be created with its own branch to complete the remaining work. Do not
create additional branches for the same ticket.

Pull Request
^^^^^^^^^^^^

Before a pull request can be merged, the full verification pipeline must pass. Run
:code:`make test` from the project root and ensure every step succeeds.  What that
pipeline does is described under `Verification of Completed Work`_.

Reviewers must also check every use of :code:`pragma: no cover`, :code:`noqa`,
:code:`type: ignore`, and :code:`nosec` in the changed code.  Each of these exceptions
must have a clear, valid reason.  For :code:`nosec` (or when the comment would be too
long on one line), the justification may appear on the line above the exception
comment.


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

We use `Poetry <https://python-poetry.org>`_ to manage Python dependencies.  Declared
dependencies live in the root :code:`pyproject.toml`; the exact versions used in the
build are pinned in :code:`poetry.lock`.  We allow loose version constraints in
:code:`pyproject.toml` (e.g. :code:`^2.11`); the lock file is the source of truth when
Docker images are built, and we do not update the lock file during test, build, or
deployment.  Each Docker image installs a clean set of dependencies from the lock file
so that we avoid untracked or drifting dependencies.

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
  standard `SemVer <https://semver.org>`_ format for production releases.
  :code:`MAJOR.MINOR.PATCH`
- If we are deploying from any other branch we ensure the version follows our standard
  for dev versions. :code:`MAJOR.MINOR.PATCH-dev.ATTEMPT`

Major, Minor, Patch, and Attempt must all be integer numbers.

Verify Feature Tests Were Added
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On any branch other than :code:`main`, we require a feature test file for the ticket.
The pipeline derives the ticket id from the branch name and the project name from
:code:`pyproject.toml`, then looks in each subproject's :code:`feature_tests` folder
for a file named :code:`test_{ticket_id}_{project_name}.py`.  That file must exist and
must define at least one test function (a line containing :code:`def test_`).  Pull
request reviewers are responsible for ensuring the test actually validates the intended
behavior.  In rare cases (e.g. a performance-only change with no behavior change),
writing a meaningful test may not be feasible; in those cases the developer must add a
comment in the file explaining what validation was done and why a real test is not
possible, and may add a minimal passing test so this check still passes.

See :doc:`testing_style_guide` for the full conventions around how feature tests should
be written.

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

developer_tooling.rst
'''''''''''''''''''''

We require that every target defined in the root :code:`Makefile` is documented in the
developer tooling page.

Check Hyperlinks are Valid
''''''''''''''''''''''''''

As long as we are not testing a commit on :code:`main` we check to make sure that all
hyperlinks in the :code:`.rst` files are valid.  We don't check if we are on main,
because we want to be able to rebuild an old version of our pipeline even if a
referenced website has changed URLs since it was first built.

General Python Package Validation Strategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The design-level conventions for source code — how to structure modules, when to use
classes vs functions, how to define data models, and more — are described in the
:doc:`source_code_style_guide`.  The tooling below enforces the surface-level rules
automatically; the style guide covers everything the tools cannot check.

There is a general validation strategy that the following python packages go through:
 - :doc:`build_support`
 - :doc:`infra`
 - :doc:`assembly_design`
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
Static Type Checking - MyPy
'''''''''''''''''''''''''''

We run :code:`mypy` on every package to ensure that typing is enforced.  The version
and configuration live in :code:`pyproject.toml` under :code:`[tool.mypy]`.  We use the
Pydantic plugin and enable a strict set of checks: disallow untyped defs and untyped
calls, warn on redundant casts and return of :code:`Any`, disallow unimported
:code:`Any`, and enable error codes such as redundant-self, possibly-undefined,
truthy-bool, explicit-override, and others.  Any use of :code:`type: ignore` must be
explained to the satisfaction of the pull request reviewer.

Bandit Security Tests
'''''''''''''''''''''

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
    the module is described, if there are any in the module.

Functions and Methods
.....................

  * An :code:`Args` section exists where the function or method's arguments are given a
    description.
  * Either a :code:`Returns` or :code:`Yields` section exists where the result of the
    function or method is described.

Testing Source Code
'''''''''''''''''''
All subprojects with source code follow the same testing standards, described in full in
the :doc:`testing_style_guide`.  The summary below covers the enforcement mechanics;
consult that document for philosophy, conventions, and examples.

The :code:`process_and_style_enforcement` package in this project consists entirely of
test code that is run to enforce our development practices.  There is no source code to
test.

Unit Tests
""""""""""
For each subproject we test each src file with a corresponding test file in the unit
test folder of the subproject.  The test file must be named :code:`test_{src_file_name}`
and mirror the directory structure of :code:`src/`.  Each src file must have 100%
branch and line coverage when its corresponding test file is executed in isolation.

After all individual files are checked for 100% coverage we run all unit tests for the
subproject at once and generate test reports that we put in the subproject's report
folder.

Feature Tests
"""""""""""""
For each subproject we run all the feature tests that have been written for the
subproject.  When running these tests we generate a test report that we put in the
subproject's report folder.  Feature tests evaluate the software from the outside,
through the same interface that real users have access to (currently a CLI, later an
API, eventually a live service instance).  We require all feature tests to pass and all
test files must have 100% coverage to prevent dead code from persisting.


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
