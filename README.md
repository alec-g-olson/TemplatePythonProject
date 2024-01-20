# Template Project

This project exists to give me and anyone else who would like to use it a template to work off of
that has a decent testing pipeline that is platform independent.

The basic philosophy of this repo is that every part of the CI/CD pipeline should be controlled in
the [Makefile](Makefile), with all relevant steps running in Docker with well versioned requirements.
This means that anyone on any system should be able to run `make test`, or `make push` and have the
same environment and execution steps locally or on whatever CI/CD service you are working with.

This is licensed with the MIT No Attribution License, which allows anyone to take the code and do
whatever they want with no need for attribution or requirement to keep your projects open source.


## Primary Services

This section of the read-me template is stuff that I find useful when initially documenting a project.

What are the primary services of the artifact generated by this repo?

### API

Is there an API?

### Other Service

Are there other services?

# Getting Started

To get started with this repository the developer must install the following:
  
  - [Docker](https://docs.docker.com/)
  - [Make](https://www.gnu.org/software/make/)
  - [Python](https://www.python.org/)

To ensure that you have installed all components correctly run `make lint test` from the projects root directory.

## Development Environment Setup

Jump to:
 - [PyCharm](#pycharm)
 - [VS Code](#vs-code)

### PyCharm

If you prefer to use the PyCharm IDE use the following instructions to get setup.

#### PyCharm: Setting the Python Interpreter

In the root directory for this project run `make build_dev_environment` to build the docker image with the correct
interpreter.  Once you have done this go to PyCharm's Interpreter Settings and navigate to "Add Interpreter > On 
Docker". Select "Pull or use existing" and fill the "image tag" field with `template_python_project:dev`.  Click 
"Next", wait for the image to load, click "Next", ensure that "System Interpreter" is selected on the left with 
`/usr/local/bin/python3`, and finally click "Create".  Then hit "Apply" on PyCharm's Interpreter Settings page and 
enjoy!

Note: The image name is pulled from [pyproject.toml](pyproject.toml).  If you change `template_python_project` to
something else you must build a new image and reset the interpreter.  You'll also need to update this README.

#### PyCharm: Setting Src and Test Folders

There are two source folders in this project, `src` and `build_support/build_src`.  For each of them you need to 
right-click on the folder in the project view.  There will be a `Mark Directory as` option.  Hover over that and then
select `Sources Root`.

There are two test folders in this project, `test`, and `build_support/build_test`.  For each of them you will repeat
the process described for the source folders, but instead of selecting `Sources Root`, you will mark these as `Test
Sources Root`.

#### PyCharm: Configuring PyCharm to Use Pytest

By default, PyCharm uses `unittest`.  This project uses `pytest` and PyCharm needs to be configured to default to it.
To do this go to PyCharm's Settings and on the left side select "Tools" and then "Python Integration Tools".  On this
pane there should be a "testing" section with a drop-down menu.  Select `pytest` from the drop-down and click "Apply"
and then "OK".

#### PyCharm: Checking Your Work by Running the Tests

Right click "test" in the project structure window.  Then click "Run 'pytest in test'".  All tests should run and pass.
If there are any issues it is an indication that setup was not followed correctly.  Ensure that the docker image was
built correctly, PyCharm correctly picking up its interpreter, and that PyCharm is using pytest.

### VS Code

If you prefer to use the VS Code IDE use the following instructions to get setup.

#### VS Code: Setting the Python Interpreter

Someone else can add instructions here.

#### VS Code: Setting Src and Test Folders

Someone else can add instructions here.

#### VS Code: Configuring VS Code to Use Pytest

Someone else can add instructions here.

#### VS Code: Checking Your Work by Running the Tests

Someone else can add instructions here.

## Working in this Repository

When working in this repository make sure that everything you do is ultimately recorded in a make command.  Our goal is
to have the test pipelines be a light script wrapping `make test` for whatever CI/CD environment we run in, and our
deployment pipelines to be wrapping `make push`.  These commands should run in the same environments locally, during
test and deployment, and in the cloud.  Put another way, if a new dev clones this repo, installs the technologies 
listed in the "Getting Started", and runs `make test` it should work.  And the only thing that should fail if they run
`make push` is our check that the version they have has already been pushed.

### Selected Build Commands
| Command                      | Description                                                     |
|------------------------------|-----------------------------------------------------------------|
| `make clean`                 | Clears the build folder, removing all intermediate build files. |
| `make build_dev_environment` | Builds the docker with the dev environment.                     |
| `make lint`                  | Runs the lint commands on this repo.                            |
| `make test`                  | Runs                                                            |
| `make build_artifact`        | Builds the artifact produced by this repo.                      |
| `make push`  TBD             | Pushes the artifact produced by this repo to prod.              |

### Tools Enforcing Dev Standards
 - [PyTest and PyTest-Cov](#pytest-and-pytest-cov)
 - [iSort](#isort)
 - [Black](#black)
 - [PyDocStyle](#pydocstyle)
 - [Flake8](#flake8)
 - [MyPy](#mypy)

#### PyTest and PyTest-Cov
We enforce 100% coverage of files in the src and test folders in this repo.  If there is a line, branch, or function
that is going to be too difficult to test you can add a `#pragma: no cover` comment on that line, and it will be
ignored.

#### iSort

[iSort](https://pycqa.github.io/isort/) is used to enforce consistent import statement order.  This cedes all 
authority on the "correct" way to order import statements to iSort so that there are not arguments between devs.

We enforce import sorting on all src, test, and build_support python files.

#### Black

Similar to how we have given authority over import order to iSort, we have given authority over code formatting to 
[Black](https://black.readthedocs.io/).

We enforce import sorting on all src, test, and build_support python files.

#### PyDocStyle

[PyDocStyle](https://www.pydocstyle.org/) enforces documentation.  Requires devs to write a docstring for every
function, class, module, etc... and enforces some style guides on those docstrings.

If we can find a way to enforce documenting the inputs and return values of functions I'd love to add it.

We only enforce docstrings on python files in the src folder.

#### Flake8

[flake8](https://flake8.pycqa.org/) enforces some basic code patterns and style.

We enforce flake8 requirements on all src, test, and build_support python files.

#### MyPy

[MyPy](https://mypy.readthedocs.io/) enforces typing.

We enforce typing on all src, test, and build_support python files.

## Technologies and Frameworks

Summarize at a high level the technologies and frameworks used.

### Major Technologies

Explain the major technologies is more detail.  Add headers as needed.

### Other tools

Are there other tools that augment the major technologies?

# Versioning

SemVer!  This is managed in [pyproject.toml](pyproject.toml)

# Creating a Release

Run `make push`.