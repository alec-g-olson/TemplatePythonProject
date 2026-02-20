Sub-Projects
============

These projects are used with each other to enforce standards. Documentation on this page
is intended to give a high level overview of the goals of each sub-project.  To find
information on implementation or the philosophical principles behind the organization of
the sub-projects go to the subprojects code documentation.


Build Support
-------------

The contents of this folder are responsible for executing our CI/CD pipeline.  It
contains many tasks that are linked together in a DAG to execute in order.

To execute these tasks you should run commands from the project's Makefile such as
:code:`make test` or :code:`make push` to ensure that you are running the commands in the correct
docker container with the correct values (such as path to project) for your system.

The goal of this project is that everything is handled and run in controlled docker
environments which make it so that you can run the CI/CD pipeline on any machine and
ensure that the environment will be the same.

There are some elements of our process that don't have corresponding off-the-shelf 3rd
party tools we can use for enforcement.  To keep our project organized we have added
both process and style enforcement test suites to our build support tests.

:doc:`build_support`

Infra
-----

Pulumi stuff!

:doc:`infra`

Pypi Package
------------

This is the template project pypi package.  It's pretty useless on it's own, and you
should replace it with useful code as soon as you start a new project!

Also update this description!

:doc:`template_python_project`
