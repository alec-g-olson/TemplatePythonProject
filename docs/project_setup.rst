Getting Started
===============

To get started with this repository the developer must install the following:

- `Docker <https://docs.docker.com>`_
- Make

To ensure that you have installed all components correctly run :code:`make lint` from
the project's root directory.


DO NOT MODIFY ANY OF THE SOURCE FILES BEFORE YOU HAVE SUCCESSFULLY RUN
:code:`make lint`.

Development Environment Setup
-----------------------------

Jump to:

- `Pycharm`_
- `VS Code`_

PyCharm
~~~~~~~

If you prefer to use the PyCharm IDE use the following instructions to get setup.

PyCharm: Setting the Python Interpreter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the root directory for this project run :code:`make setup_dev_env` to build the
docker image with the correct interpreter.
Once you have done this go to PyCharm's Interpreter Settings and navigate to
:code:`Add Interpreter` > :code:`On Docker`.
Select :code:`Pull or use existing` and fill the :code:`image tag` field with
:code:`template-python-project:dev`.
Click :code:`Next`, wait for the image to load, click :code:`Next`, ensure that
:code:`System Interpreter` is selected on the left with :code:`/usr/local/bin/python3`,
and finally click :code:`Create`.
Then hit :code:`Apply` on PyCharm's Interpreter Settings page and enjoy!

PyCharm: Setting Src and Test Folders
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each of the following source folders you need to right-click on the
folder in the project view. There will be a :code:`Mark Directory as` option.
Hover over that and then select :code:`Sources Root`.

- :code:`build_support/src`
- :code:`docs/sphinx_conf`
- :code:`pypi_package/src`

For each of the following test folders you will repeat the process described for the
source folders, but instead of selecting :code:`Sources Root`, you will mark these as
:code:`Test Sources Root`.

- :code:`build_support/test`
- :code:`pypi_package/test`

PyCharm: Configuring PyCharm to Use Pytest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Depending on your version of Pycharm, it could default to using :code:`unittest`.
This project uses :code:`pytest` and PyCharm needs to be configured to default to it.
To do this go to PyCharm's Settings and navigate to
:code:`Tools | Python Integrated Tools` where you should see a drop-down menu labeled
:code:`Testing`.
Select :code:`pytest` from the drop-down and click "Apply" and then "OK".

PyCharm: Adjusting Docstring Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Depending on your version of Pycharm, it could default to using  :code:`Plain` docstring
formats, but this project uses :code:`Google` style docstrings.
PyCharm can be configured to enable stub generation using the Google docstring format.
Go to PyCharms Settings and navigate to :code:`Tools | Python Integrated Tools` where
you should see a drop-down menu labeled :code:`Docstring format`.
Select :code:`Google` from the drop-down and click "Apply" and then "OK".

PyCharm: Setting Vertical Ruler to 88
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Pycharm sets the vertical ruler to position 120, which is much longer than
the 88 characters that we set Ruff to allow.
Go to PyCharms Settings and navigate to :code:`Editor | Code Style` where you should see
a field labeled `Hard Wrap at` with a value of 120.
Change this value to 88 and click "Apply" and then "OK".

PyCharm: Checking Your Work by Running the Tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Right click :code:`pypi_package/test` in the project structure window.
Then click :code:`Run 'pytest in test'`.
All tests should run and pass.
If there are any issues it is an indication that setup was not followed correctly.
Ensure that the docker image was built correctly, PyCharm is correctly picking it as its
interpreter, and that PyCharm is using pytest.

VS Code/Cursor AI
~~~~~~~~~~~~~~~~~

I've never liked VS Code and so I didn't spend the time required to figure this out.
If someone wants to use VS Code please add instructions here once you've figured out
how to setup using pytest with a docker interpreter and how to set the PYTHONPATH for
VS Code to correctly find the source and test folders.


Working in this Repository
--------------------------

This repository includes a number of prebuilt commands that make it easier to
execute development tasks in standardized ways.

:doc:`Developer Tooling <developer_tooling>`

