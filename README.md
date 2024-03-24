[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# Template Project

This project exists to give me and anyone else who would like to use it a template to
work off of that has a decent testing pipeline that is platform independent.

This project is licensed with The Unlicense, which puts this project into the public
domain.  Anyone can take this code and do anything they want for profit or personal use
with no need for attribution or requirement to keep your projects open source.  When you
make a new project based on this template you can use any license you want, and only the
code that came from this template will be part of the public domain, unless you choose 
to use a license that puts the rest of your new project into the public domain.

### Goals of Template Project

The platonic ideal of a well controlled project is that you should be able to run a 
1-line command to build your entire system from scratch, upgrade to a new 
version, or roll-back to a previous version.  The developers of this template project 
also believe that unless development practices are enforced by code they are not 
enforced.  This template project strives to provide a well organized set of practically
applicable patterns for scalable project development in a completely controlled 
environment.

Running tests and deployments should be as simple as `make test` or `make push`
regardless of whether you are using a personal machine or a service account running in
a cloud VM.

#### Enforcement of Development Practices

The enforcement of development practices is done in the CI/CD pipeline and controlled in
the [build_support](build_support/src/build_support) package.  Any practices the
development team wants to enforce should be added into the tasks implemented here, or
in another location that is called and run by a task in the CI/CD pipeline.  For example
the ValidatePythonStyle Task in the 
[validation_tasks.py](build_support/src/build_support/ci_cd_tasks/validation_tasks.py)
module makes a call that runs the tests in the 
[process_and_style_enforcement](process_and_style_enforcement) directory.

#### Enforcement of Development and Production Environments

This project goes to great lengths to ensure that all commands are run in controlled
environments.  This is done by running as many commands as possible in docker 
containers.  The build container is used to run the build pipeline, and makes many
calls that execute commands in the dev, pulumi, or prod containers.  When making these
calls this project uses a Docker outside of Docker (DooD) strategy.

This project has a [Makefile](Makefile) that exists to make executing
CI/CD tasks and getting local variables (such as the local filepath to the project) 
easy.  There are some tasks that have to be executed on the local system, such as
building the build container, and in these situations these tasks should be added as
commands within the makefile.

### Organization of Template Project

For the sake of centralized enforcement this template project is structured as a 
monorepo.  Once you have created your own project from this template you can break it up
as you see fit.  There are 4 top-level folders that are worth discussing:

- [build_support](build_support)
  - Contains all the tasks that can be run as part of CI/CD or development
  - [execute_build_steps.py](build_support/src/build_support/execute_build_steps.py)
  Contains the "main" that should be called within the build container to run tasks.
  - [report_build_var.py](build_support/src/build_support/report_build_var.py)
  Contains the "main" that should be called within the build container to report 
  variables.
- [process_and_style_enforcement](process_and_style_enforcement)
  - The tests that are run as part of the ValidatePythonStyle task.  Tests should be 
  added here when there isn't an off the shelf tool for enforcing style or process that 
  the devs want to enforce.
- [pulumi](pulumi)
  - The pulumi code that sets up and manages cloud resources and deployments.
- [pypi_package](pypi_package)
  - The pypi package that will contain our business logic and will be deployed to
  production environments. 

### Scope of Template Project

This project wants to provide a template project that is useful for start-ups or other
small organizations, so they can start from a well managed and controlled codebase.
Hopefully this will prevent the painful process of growing to the point that controls
are needed and then having to enforce controls and practices onto an unwieldy codebase.

In order to achieve this, this template project must provide practically useful software
patterns that can be easily extended to meet business needs.

#### Architecture Layers

The all implementations will be dictated by the general design philosophy we take.  We
have tried to balance general applicability with useful snippets of example code.  The
following 3-layer architecture will be managed as best we can in 
[pypi_package](pypi_package) and implemented across all production environments.

 - API Layer (Not implemented)
 - Engine Layer (Not implemented)
   - Fast tasks - Less than 10ms in API layer
   - Medium tasks - Less than 2 minutes but more than 10ms (Not implemented)
   - Long tasks - More than 2 minutes (Not implemented)
 - Persistence Layer (Not implemented)
   - Files - e.g. (GCS, S3, etc...)
   - Databases
     - Structured - e.g. mySQL
     - Semi-structured - e.g. PostgreSQL
     - Unstructured - e.g. MongoDB
 
#### Environments this Template Strives to Support

Below is a list of environments that we hope to support:

 - Local Deployment to Docker Compose (Not implemented)
 - AWS (Not implemented)
 - GCP (Not implemented)
 - Azure (Not implemented)

#### Additional Control this Template Tries to Provide

We want to make it so that this project can manage the CI/CD rules on whatever platform
the team is developing on.  So we strive to make it so that when a new project is set up
the source code management is also set up and controlled.

 - GitHub setup (Not implemented)
 - Azure DevOps setup (Not implemented)
 - Atlassian setup (Not implemented - no Pulumi support)
 - User account management including permissions (Not implemented)

### Creating a New Project From This Template

In order to create a new project from this template first modify the fields in the 
[project_settings.yaml](build_support/new_project_settings.yaml) to what ever values you
need and then run `make make_new_project`.  This will change the following files and 
folders in the ways listed below:

 - LICENSE
   - Use the specified license template to make a new license
   - Use the provided organization name and email (if applicable)
   - Use the current year for copyright (if applicable)
 - pypi_package:
   - Change the name of the package in the src folder to the new project name.
 - [pyproject.toml](pyproject.toml):
   - Change the project name.
   - Reset the version number of this project to `0.0.0`.
   - Change the license to the specified license.
   - Update the project Authors.
   - Update the name of the folder to include when building a pypi package.

## Primary Services

This section of the read-me template is stuff that I find useful when initially 
documenting a project.

What are the primary services of the artifact generated by this repo?

### API

Is there an API?

### Other Service

Are there other services?

# Getting Started

To get started with this repository the developer must install the following:
  
  - [Docker](https://docs.docker.com/)
  - [Make](https://www.gnu.org/software/make/)

To ensure that you have installed all components correctly run `make lint` from the
project's root directory.

## Development Environment Setup

Jump to:
 - [PyCharm](#pycharm)
 - [VS Code](#vs-code)

### PyCharm

If you prefer to use the PyCharm IDE use the following instructions to get setup.

#### PyCharm: Setting the Python Interpreter

In the root directory for this project run `make setup_dev_env` to build the 
docker image with the correct interpreter.  Once you have done this go to PyCharm's 
Interpreter Settings and navigate to "Add Interpreter > On Docker". Select "Pull or use 
existing" and fill the "image tag" field with `template_python_project:dev`.  Click
"Next", wait for the image to load, click "Next", ensure that "System Interpreter" is 
selected on the left with `/usr/local/bin/python3`, and finally click "Create".  Then 
hit "Apply" on PyCharm's Interpreter Settings page and enjoy!

#### PyCharm: Setting Src and Test Folders

For each of the following source folders you need to right-click on the
folder in the project view. There will be a `Mark Directory as` option.  Hover over that
and then select `Sources Root`.

- [build_support/src](build_support/src)
- [pulumi/src](pulumi/src)
- [pypi_package/src](pypi_package/src)

For each of the following test folders you will repeat the process described for the 
source folders, but instead of selecting `Sources Root`, you will mark these as 
`Test Sources Root`.

- [build_support/test](build_support/test)
- [process_and_style_enforcement/test](process_and_style_enforcement/test)
- [pypi_package/test](pypi_package/test)

#### PyCharm: Configuring PyCharm to Use Pytest

By default, PyCharm uses `unittest`.  This project uses `pytest` and PyCharm needs to be
configured to default to it. To do this go to PyCharm's Settings and navigate to 
`Tools | Python Integrated Tools` where you should see a drop-down menu labeled 
`Testing`.  Select `pytest` from the drop-down and click "Apply" and then "OK".

#### PyCharm: Adjusting Docstring Settings

By default, Pycharm uses `Plain` docstring formats, but this project uses Google style
docstrings. PyCharm can be configured to enable stub generation using the Google 
docstring format.  Go to PyCharms Settings and navigate to 
`Tools | Python Integrated Tools` where you should see a drop-down menu labeled 
`Docstring format`.  Select `Google` from the drop-down and click "Apply" and then "OK".

#### PyCharm: Setting Vertical Ruler to 88

By default, Pycharm sets the vertical ruler to position 120, which is much longer than
the 88 characters that we set `Ruff` to allow.  Go to PyCharms Settings and navigate to
`Editor | Code Style` where you should see a field labeled `Hard Wrap at` with a value 
of 120.  Change this value to 88 and click "Apply" and then "OK".

#### PyCharm: Checking Your Work by Running the Tests

Right click `bulid_support/test` in the project structure window.  Then click 
"Run 'pytest in test'". All tests should run and pass. If there are any issues it is an 
indication that setup was not followed correctly.  Ensure that the docker image was 
built correctly, PyCharm correctly picking up its interpreter, and that PyCharm is 
using pytest.

### VS Code

If you prefer to use the VS Code IDE use the following instructions to get setup.

[Ticket for Adding VS Code Setup Instructions](https://github.com/alec-g-olson/TemplatePythonProject/issues/68)

# Working in this Repository

When working in this repository make sure that as many instructions as possible are
recorded in [build_support](build_support) tasks, and if that isn't possible we must
record them in a make command.  Because there is a great deal of convince in using make
commands instead of requiring local environment values (such as path to the project), 
it is useful for all instructions to run through make commands. 

The following commands are a subset of the commands available that are particularly
useful to new developers working in this repo.

## Selected Build Commands
| Command                      | Description                                                      |
|------------------------------|------------------------------------------------------------------|
| `make clean`                 | Clears the build folder, removing all intermediate build files.  |
| `make docker_prune_all`      | Deletes all docker containers, images, and caches on machine.    |
| `make open_dev_docker_shell` | Opens a shell within a dev docker container.                     |
| `make setup_dev_env`         | Builds the docker with the dev environment.                      |
| `make lint`                  | Runs the lint commands on this repo.                             |
| `make test`                  | Runs all build, process, and style tests for this repo.          |
| `make build`                 | Builds the artifacts produced by this repo.                      |
| `make push`  TBD             | Pushes the artifacts produced by this repo to prod.              |

## Tools Enforcing Dev Standards
 - [Poetry](#poetry)
 - [PyTest and PyTest-Cov](#pytest-and-pytest-cov)
 - [Ruff](#ruff)
 - [Process and Style Enforcement](#process-and-style-enforcement)
 - [MyPy](#mypy)
 - [Bandit](#bandit)

### Poetry

[Poetry](https://python-poetry.org) is a tool used for managing dependencies and
building/publishing packages.

The dependencies are listed in [pyproject.toml](pyproject.toml), and should not be
edited unless you are in a shell that was opened with `make open_dev_docker_shell`.
Once a shell has been opened you can edit the requirements.  Once you are done editing
you need to run `poetry lock --no-update` in order for the lockfile to be synced with
the new requirements.  Once this command executes without error, exits from the shell.

Anytime you run a poetry process outside the CI/CD pipeline (`update`, `add`, etc..)
you should follow a similar pattern of first opening a dev shell and then closing the
shell when you are done.

### PyTest and PyTest-Cov
We enforce 100% coverage of files in the src and test folders in this repo.  If there is
a line, branch, or function that is going to be too difficult to test you can add a 
`#pragma: no cover` comment on that line, and it will be ignored.

### Ruff

[Ruff](https://docs.astral.sh/ruff/) is used by this project as both a formatter and a
linter.

When linting we run all stable rules that are compatible with the Ruff Formatter.
Because Ruff is under active development and the list of new tests and stable tests
is changing with some frequency we want to pin Ruff to a specific version, which is much
stricter than we treat most packages we manage in poetry.

Ruff is a drop in replacement for:
- isort
- black
- pydocstyle
- pyupgrade
- flake8
- autoflake

### Process and Style Enforcement

[process_and_style_enforcement/test](process_and_style_enforcement/test) contains a 
number of tests that we have implemented to enforce standards for which no off the shelf
tools exist.  Additional style or process enforcement without off the shelf tooling 
should go here.

### MyPy

[MyPy](https://mypy.readthedocs.io/) enforces typing.

We enforce typing on all `src` and `test` python files.

### Bandit

[Bandit](https://bandit.readthedocs.io/en/latest/) is a static analysis tool that
identifies possible security threats.

# Technologies and Frameworks

Summarize at a high level the technologies and frameworks used.

## Major Technologies

Explain the major technologies is more detail.  Add headers as needed.

## Other tools

Are there other tools that augment the major technologies?

# Versioning

SemVer!  This is managed in [pyproject.toml](pyproject.toml)

# Creating a Release

Run `make push`.