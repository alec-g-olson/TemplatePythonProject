MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DOCKERFILE = $(MAKEFILE_DIR)Dockerfile
PYPROJECT_TOML = $(MAKEFILE_DIR)pyproject.toml
PROJECT_NAME = $(shell awk -F'[ ="]+' '$$1 == "name" { print $$2 }' $(PYPROJECT_TOML))
DOCKER_BUILD_IMAGE = $(PROJECT_NAME):build
DOCKER_DEV_IMAGE = $(PROJECT_NAME):dev
DOCKER_PROD_IMAGE = $(PROJECT_NAME):prod
DOCKER_PULUMI_IMAGE = $(PROJECT_NAME):pulumi
DOCKER_REMOTE_PROJECT_ROOT = /usr/dev
USER_ID = $(shell id -u)
USER_GROUP = $(shell id -g)
USER_NAME = $(shell id -un)
USER = $(USER_ID):$(USER_GROUP)


BASE_DOCKER_BUILD_ENV_COMMAND = docker run --rm --workdir=$(DOCKER_REMOTE_PROJECT_ROOT) \
-e PYTHONPATH=/usr/dev/build_support/build_src \
-v ~/.ssh:/home/$(USER_NAME)/.ssh:ro \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $(MAKEFILE_DIR):$(DOCKER_REMOTE_PROJECT_ROOT)

DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) $(DOCKER_BUILD_IMAGE)
INTERACTIVE_DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) -it $(DOCKER_BUILD_IMAGE)

SHARED_BUILD_VARS = --non-docker-project-root $(MAKEFILE_DIR) --docker-project-root $(DOCKER_REMOTE_PROJECT_ROOT)

EXECUTE_BUILD_STEPS_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) python build_support/build_src/execute_build_steps.py \
$(SHARED_BUILD_VARS) --user-id $(USER_ID) --group-id $(USER_GROUP) --local-username $(USER_NAME)

GET_BUILD_VAR_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) python build_support/build_src/report_build_var.py \
$(SHARED_BUILD_VARS) --build-variable-to-report

.PHONY: push
push: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) push

.PHONY: push_pypi
push_pypi: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) push_pypi

.PHONY: build_pypi
build_pypi: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) build_pypi

.PHONY: test
test: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) test

.PHONY: autoflake
autoflake: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) autoflake

.PHONY: lint
lint: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) lint

.PHONY: test_without_style
test_without_style: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) test_without_style

.PHONY: open_build_docker_shell
open_build_docker_shell: setup_build_envs
	$(INTERACTIVE_DOCKER_BUILD_ENV_COMMAND) /bin/bash

.PHONY: open_dev_docker_shell
open_dev_docker_shell: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) build_dev
	$(eval INTERACTIVE_DEV_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) get-interactive-dev-docker-command))
	$(INTERACTIVE_DEV_COMMAND) /bin/bash

.PHONY: open_prod_docker_shell
open_prod_docker_shell: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) build_prod
	$(eval INTERACTIVE_PROD_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) get-interactive-prod-docker-command))
	$(INTERACTIVE_PROD_COMMAND) /bin/bash

.PHONY: open_pulumi_docker_shell
open_pulumi_docker_shell: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) build_pulumi
	$(eval INTERACTIVE_PULUMI_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) get-interactive-pulumi-docker-command))
	$(INTERACTIVE_PULUMI_COMMAND) /bin/bash

.PHONY: clean
clean: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) clean

.PHONY: make_new_project
make_new_project: setup_build_envs
	$(EXECUTE_BUILD_STEPS_COMMAND) make_new_project

.PHONY: setup_build_envs
setup_build_envs:
	docker login
	docker build --build-arg CURRENT_USER_ID=$(USER_ID) --build-arg CURRENT_USER_GROUP=$(USER_GROUP) --build-arg CURRENT_USER=$(USER_NAME) -f $(DOCKERFILE) --target build --build-arg BUILDKIT_INLINE_CACHE=1 -t $(DOCKER_BUILD_IMAGE) $(MAKEFILE_DIR)

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force
