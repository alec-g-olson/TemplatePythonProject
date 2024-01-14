FROM python:3.11.4

RUN pip install --upgrade pip==23.2.1
RUN python -m pip install pip-tools==7.1.0
COPY requirements.in requirements.in
COPY requirements-dev.in requirements-dev.in
COPY requirements.txt requirements.txt
RUN pip-compile --output-file requirements.txt requirements.in requirements-dev.in
RUN pip-sync