FROM python:3.11.4 AS base

# make sure to update build.system.requries poetry version in pyproject.toml
ENV POETRY_VERSION="1.7.1"
ENV POETRY_HOME="/opt/poetry"

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install --upgrade pip==23.3.2
RUN pip install poetry==$POETRY_VERSION

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN poetry config virtualenvs.create false

FROM base AS dev

RUN poetry install

FROM base as prod

RUN poetry install --without dev