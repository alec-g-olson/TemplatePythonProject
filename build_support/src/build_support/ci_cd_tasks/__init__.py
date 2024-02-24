"""Contains logic for all tasks that are involved in CI/CD.

These tasks are organized by the general order that builds go through.

    | * Env Setup
    | * Test (or Lint)
    | * Build Artifact
    | * Push Artifact

This is done to prevent circular dependencies.  In the past we tried to organize
these tasks by domain specific functions, but this lead to circular dependencies.

Modules:
    | env_setup_tasks.py: Tasks that setup environments for CI/CD should go here.
        e.g. Building dev docker containers, cleaning, getting git status, etc...
    | test_tasks.py: Testing tasks, these should only depend on env setup tasks.
        Testing should not be dependent on linting.
    | lint_tasks.py: Linting tasks.  It's okay for some of these to depend on some
        tests, because no tests should depend on linting.
    | build_tasks.py: Tasks that build artifacts that will be pushed.  If a docker
        image is being pushed as an artifact it should be built here, not in env setup.
    | push_tasks.py: Tasks that push artifacts to their repos.  All other push tasks
        should depend on the "PushTags" task, because the new tag should be pushed to
        git before any artifacts are pushed.  If an artifact push fails after the git
        tags have been pushed then a new version should be used for the next attempted
        push.
"""
