FROM python:3.12.1 AS base

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

RUN poetry install --with dev

FROM base as prod

RUN poetry install

FROM base as pulumi

RUN poetry install --with pulumi

ENV PULUMI_VERSION="3.101.1"
ENV PULUMI_HOME="/root/.pulumi/"

ENV PATH="$PULUMI_HOME/bin:$PATH"

RUN curl -fsSL https://get.pulumi.com | sh -s -- --version $PULUMI_VERSION
