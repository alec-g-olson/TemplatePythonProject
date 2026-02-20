Developer Tooling
=================

This project goes to great lengths to make sure everything works on everyone else's
machine.  To do that as many elements of the build and development process are recorded
as :doc:`Build Support <build_support>` tasks.  However, there are times that we need
machine specific environment variables (such as the directory location) and so we use
a Makefile to get these variables and pass them to the docker commands.  Because of this
all of the standard commands are accessed via `make` commands.

Everything runs in Docker with Python dependencies managed by Poetry. Running Poetry
commands outside the intended context can leave the environment in a bad state. Follow
the instructions below when changing dependencies.

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


Running Poetry Commands
-----------------------

Docker, Poetry, and :code:`pyproject.toml` are set up so that any command that
changes :code:`poetry.lock` (e.g. :code:`poetry lock`) must be run inside the dev
container.

#. Run :code:`make open_dev_docker_shell` to start a dev shell.
#. From that shell, run the Poetry commands that update :code:`poetry.lock`.
#. Edit :code:`pyproject.toml` in your usual editor; the project is mounted into the
   container, so changes are visible both inside and outside the shell.
#. Exit the shell when done. New containers will use the updated
   :code:`poetry.lock`.

If In A Bad State
~~~~~~~~~~~~~~~~~

If :code:`pyproject.toml`, :code:`poetry.lock`, and the Dockerfile are out of sync:

#. Stash or discard your local changes to :code:`pyproject.toml` and
   :code:`poetry.lock`, then reset them to the last known-good commit.
#. Run :code:`make open_dev_docker_shell`.
#. In the dev shell, restore the :code:`pyproject.toml` changes you want (from stash
   or commits), then run the needed Poetry commands and finish with :code:`poetry lock`.
#. Exit the shell. The next Docker build should install Poetry-managed packages
   correctly.
