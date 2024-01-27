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

FROM base AS build

RUN poetry install --with build
# Add Docker's official GPG key:
RUN apt-get update
RUN apt-get install ca-certificates curl gnupg
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

FROM base AS dev

RUN poetry install --with dev

FROM base as prod

RUN poetry install

FROM base as pulumi

RUN poetry install --with pulumi

ENV PULUMI_HOME="/root/.pulumi/"

ENV PATH="$PULUMI_HOME/bin:$PATH"

RUN curl -fsSL https://get.pulumi.com | sh -s --
