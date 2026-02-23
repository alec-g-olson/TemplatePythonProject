Developer Tooling
=================

This project goes to great lengths to make sure everything works on everyone else's
machine.  To do that as many elements of the build and development process are recorded
as :doc:`Build Support <build_support>` tasks.  However, there are times that we need
machine specific environment variables (such as the directory location) and so we use
a Makefile to get these variables and pass them to the docker commands.  Because of this
all of the standard commands are accessed via `make` commands.

Build output verbosity is controlled by the :code:`LOG_LEVEL` environment variable.
Pass it to :code:`make` (e.g. :code:`make test LOG_LEVEL=DEBUG`) to change how much the
build prints. Three levels apply to successful runs:

* **INFO** (default): Workflow only — task list, "Starting:", run report. No command
  lines or task output.
* **DEBUG**: Level 1 plus the command line before each subprocess (e.g. the
  :code:`docker run` invocation for each task).
* **TRACE**: Level 2 plus task stdout and stderr with "stdout:" and "stderr:" labels.

On task failure, the failing command, return code, and that command's stdout and
stderr are always logged at ERROR, so they are visible at any :code:`LOG_LEVEL`.

Everything runs in Docker with Python dependencies managed by uv. Running uv
commands (e.g. :code:`uv lock`) outside the dev container can leave the environment
out of sync. Follow the instructions below when changing dependencies.

Branch-Specific Docker Image Tags
---------------------------------

Docker image tags are branch-scoped to prevent collisions when multiple ticket branches
run on the same machine.

- On :code:`main`, image tags are unsuffixed (for example
  :code:`template_python_project:build`, :code:`template_python_project:dev`,
  :code:`template_python_project:prod`).
- On non-main branches, image tags are suffixed with the branch ticket id (for example
  branch :code:`107-add-ticket-id-to-docker-image-tag` uses
  :code:`template_python_project:build-107`, :code:`template_python_project:dev-107`,
  :code:`template_python_project:prod-107`).
- The Makefile computes this via :code:`TAG_SUFFIX`, and standard :code:`make`
  commands use the computed suffix consistently.

If you run Docker commands manually, include the same suffix as your current branch or
pass :code:`TAG_SUFFIX` explicitly so you target the correct local images.

Standardized Developer Commands
-------------------------------

`make` is the convenient way we've chosen to make sure that all of the developer
commands are easily accessible.  We've documented their purpose here, and highlighted
a few important ones for people who are new to this repository.

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Command
     - Start Here
     - Description
   * - make clean
     - Yes
     - Removes the build folder and intermediate files, plus cache files used by
       third-party tools.
   * - make docker_prune_all
     - Yes
     - Removes all Docker containers, images, and caches on the machine.
   * - make open_build_docker_shell
     -
     - Opens a shell in the build Docker container.
   * - make open_dev_docker_shell
     - Yes
     - Opens a shell in the dev Docker container.
   * - make open_prod_docker_shell
     -
     - Opens a shell in the prod Docker container.
   * - make open_pulumi_docker_shell
     -
     - Opens a shell in the Pulumi Docker container.
   * - make echo_v
     -
     - Prints a Makefile variable; useful when debugging or adding new targets.
   * - make setup_build_env
     -
     - Builds the Docker image for the build environment.
   * - make setup_dev_env
     -
     - Builds the Docker image for the dev environment.
   * - make setup_prod_env
     -
     - Builds the Docker image for the prod environment.
   * - make setup_pulumi_env
     -
     - Builds the Docker image for the Pulumi environment.
   * - make uv_lock
     -
     - Updates :code:`uv.lock` in the dev container after changing
       :code:`pyproject.toml`. Builds the dev image if needed.
   * - make format
     - Yes
     - Runs code formatting for this repo.
   * - make lint
     - Yes
     - Runs linting with safe fixes only. All unit tests must pass so that fixes
       don't introduce or hide behavior changes.
   * - make lint_apply_unsafe_fixes
     -
     - Runs linting and allows Ruff to apply unsafe fixes. All tests must still pass.
   * - make test_pypi
     -
     - Runs unit tests for the :code:`pypi_package` subproject.
   * - make test_build_support
     -
     - Runs unit tests for the :code:`build_support` subproject.
   * - make test_pypi_features
     -
     - Runs feature tests for the :code:`pypi_package` subproject.
   * - make test_build_support_features
     -
     - Runs feature tests for the :code:`build_support` subproject.
   * - make test_style
     -
     - Runs style-enforcement tests for this repo.
   * - make check_process
     -
     - Runs process-enforcement tests for this repo.
   * - make type_checks
     -
     - Runs mypy for this repo.
   * - make type_check_build_support
     -
     - Runs mypy for the :code:`build_support` subproject only.
   * - make security_checks
     -
     - Runs Bandit security checks for this repo.
   * - make test
     - Yes
     - Runs all build, process, style, and security tests for this repo.
   * - make build_docs
     -
     - Builds the documentation for this repo.
   * - make build
     -
     - Builds the artifacts produced by this repo.
   * - make build_pypi
     -
     - Builds the PyPI package artifact.
   * - make push
     - Yes
     - Pushes artifacts; currently this tags the built commit with the version and
       pushes tags to the remote. **Note:** If there are uncommitted changes, this
       will add, commit, and push them so that the code on the remote matches the
       tagged build.
   * - make push_pypi
     -
     - Pushes the PyPI package artifact.


Lock file / dependency updates
------------------------------

Docker, uv, and :code:`pyproject.toml` are set up so that any command that
changes :code:`uv.lock` (e.g. :code:`uv lock`) must be run inside the dev
container.

A convenient way to update the lock file after changing dependencies in
:code:`pyproject.toml`:

.. code-block:: bash

   make uv_lock

That target builds the dev image if needed and runs :code:`uv lock` in it. Commit the
updated :code:`uv.lock`.

If you need to run the lock step without the Makefile (e.g. in a bad state), use the
dev image directly:

.. code-block:: bash

   docker run --rm -v "$(pwd):/usr/dev" -w /usr/dev template_python_project:dev uv lock

If in a bad state
~~~~~~~~~~~~~~~~~

If :code:`pyproject.toml`, :code:`uv.lock`, and the Dockerfile are out of sync:

#. Stash or discard your local changes to :code:`pyproject.toml` and
   :code:`uv.lock`, then reset them to the last known-good commit.
#. Run :code:`make uv_lock` (or :code:`make open_dev_docker_shell` and run
   :code:`uv lock` in the shell).
#. Commit the updated :code:`uv.lock`. The next Docker build will use it.
