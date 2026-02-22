FROM python:3.13.5 AS base
# If python version changed here change in pyproject.toml [project] requires-python

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1

RUN pip install --upgrade pip==26.0.1

COPY uv.lock uv.lock
COPY README.md README.md
COPY pyproject.toml pyproject.toml

FROM base AS docker_enabled

# Add Docker's official GPG key:
RUN apt-get update
RUN apt-get install -y ca-certificates curl gnupg
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin

FROM docker_enabled AS git_enabled

# create local user so local permissions can be mounted into the container
# Should be safe, but avoid pushing images or containers that are based on `git_enabled`
# As of March 24th, 2024 that is only the `build` and `dev` images and containiers

# Require args to be passed from command line, do not set default value
ARG CURRENT_USER
ARG CURRENT_GROUP
ARG CURRENT_USER_ID
ARG CURRENT_GROUP_ID
RUN groupadd --gid $CURRENT_GROUP_ID $CURRENT_GROUP || \
    groupadd --gid $CURRENT_GROUP_ID hack-group || \
    /bin/true
RUN adduser --gid $CURRENT_GROUP_ID --uid $CURRENT_USER_ID $CURRENT_USER || \
    /bin/true
RUN mkdir -p /home/$CURRENT_USER/.ssh
RUN chown -R $CURRENT_USER_ID:$CURRENT_GROUP_ID /home/$CURRENT_USER/.ssh

# Setting ownership of the mounted project to the local user lets git work without error

# Require args to be passed from command line, do not set default value
ARG DOCKER_REMOTE_PROJECT_ROOT
RUN mkdir -p $DOCKER_REMOTE_PROJECT_ROOT
RUN git config --global --add safe.directory $DOCKER_REMOTE_PROJECT_ROOT
RUN chown $CURRENT_USER_ID:$CURRENT_GROUP_ID $DOCKER_REMOTE_PROJECT_ROOT

FROM git_enabled AS build

RUN uv sync --frozen --no-install-project --extra build
ENV PATH="/.venv/bin:$PATH"

FROM docker_enabled AS dev

RUN uv sync --frozen --no-install-project --extra build --extra dev --extra pulumi
ENV PATH="/.venv/bin:$PATH"

FROM base AS prod

RUN uv sync --frozen --no-install-project
ENV PATH="/.venv/bin:$PATH"

COPY pypi_package/src /usr/dev/pypi_package/src
ENV PYTHONPATH=/usr/dev/pypi_package/src
WORKDIR /usr/dev

FROM base AS pulumi

RUN uv sync --frozen --no-install-project --extra pulumi
ENV PATH="/.venv/bin:$PATH"

# If changed here change [project.optional-dependencies] pulumi in pyproject.toml
ARG PULUMI_VERSION=3.185.0

ENV PULUMI_VERSION=$PULUMI_VERSION
ENV PULUMI_HOME="/root/.pulumi/"

ENV PATH="$PULUMI_HOME/bin:$PATH"

RUN curl -fsSL https://get.pulumi.com | sh -s -- --version $PULUMI_VERSION
