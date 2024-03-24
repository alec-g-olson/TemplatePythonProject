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
GROUP_ID = $(shell id -g)
USER_NAME = $(shell id -un)
GROUP_NAME = $(shell id -gn)
USER = $(USER_ID):$(GROUP_ID)

USER_HOME_DIR = ${HOME}
GIT_CONFIG_PATH = $(USER_HOME_DIR)/.gitconfig

ifneq ("$(wildcard $(GIT_CONFIG_PATH))","")
    GIT_MOUNT = -v ~/.gitconfig:/home/$(USER_NAME)/.gitconfig
else
    GIT_MOUNT =
endif


BASE_DOCKER_BUILD_ENV_COMMAND = docker run --rm \
--workdir=$(DOCKER_REMOTE_PROJECT_ROOT) \
-e PYTHONPATH=/usr/dev/build_support/src \
-v ~/.ssh:/home/$(USER_NAME)/.ssh:ro \
$(GIT_MOUNT) \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $(MAKEFILE_DIR):$(DOCKER_REMOTE_PROJECT_ROOT)

DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) $(DOCKER_BUILD_IMAGE)
INTERACTIVE_DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) \
-it $(DOCKER_BUILD_IMAGE)

SHARED_BUILD_VARS = --non-docker-project-root $(MAKEFILE_DIR) \
--docker-project-root $(DOCKER_REMOTE_PROJECT_ROOT)

EXECUTE_BUILD_STEPS_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) \
python build_support/src/build_support/execute_build_steps.py \
$(SHARED_BUILD_VARS) --user-id $(USER_ID) --group-id $(GROUP_ID)

GET_BUILD_VAR_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) \
python build_support/src/build_support/report_build_var.py \
$(SHARED_BUILD_VARS) --build-variable-to-report

.PHONY: push
push: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) push

.PHONY: push_pypi
push_pypi: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) push_pypi

.PHONY: build
build: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) build

.PHONY: build_docs
build_docs: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) build_docs

.PHONY: build_pypi
build_pypi: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) build_pypi

.PHONY: test
test: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) test

.PHONY: apply_unsafe_ruff_fixes
apply_unsafe_ruff_fixes: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) apply_unsafe_ruff_fixes

.PHONY: list_unsafe_ruff_fixes
list_unsafe_ruff_fixes: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) list_unsafe_ruff_fixes

.PHONY: ruff_fix_safe
ruff_fix_safe: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) ruff_fix_safe

.PHONY: lint
lint: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) lint

.PHONY: test_build_support
test_build_support: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) test_build_support

.PHONY: test_pypi
test_pypi: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) test_pypi

.PHONY: test_style
test_style: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) test_style

.PHONY: open_build_docker_shell
open_build_docker_shell: setup_build_env
	$(INTERACTIVE_DOCKER_BUILD_ENV_COMMAND) /bin/bash

.PHONY: open_dev_docker_shell
open_dev_docker_shell: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_dev_env
	$(eval INTERACTIVE_DEV_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) interactive-dev-docker-command))
	$(INTERACTIVE_DEV_COMMAND) /bin/bash

.PHONY: open_prod_docker_shell
open_prod_docker_shell: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_prod_env
	$(eval INTERACTIVE_PROD_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) interactive-prod-docker-command))
	$(INTERACTIVE_PROD_COMMAND) /bin/bash

.PHONY: open_pulumi_docker_shell
open_pulumi_docker_shell: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_pulumi_env
	$(eval INTERACTIVE_PULUMI_COMMAND := $(shell $(GET_BUILD_VAR_COMMAND) interactive-pulumi-docker-command))
	$(INTERACTIVE_PULUMI_COMMAND) /bin/bash

.PHONY: clean
clean: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) clean

.PHONY: make_new_project
make_new_project: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) make_new_project

.PHONY: setup_dev_env
setup_dev_env: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_dev_env

.PHONY: setup_prod_env
setup_prod_env: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_prod_env

.PHONY: setup_pulumi_env
setup_pulumi_env: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) setup_pulumi_env

.PHONY: setup_build_env
setup_build_env:
	docker login
	docker build \
--build-arg DOCKER_REMOTE_PROJECT_ROOT=$(DOCKER_REMOTE_PROJECT_ROOT) \
--build-arg CURRENT_USER_ID=$(USER_ID) \
--build-arg CURRENT_GROUP_ID=$(GROUP_ID) \
--build-arg CURRENT_USER=$(USER_NAME) \
--build-arg CURRENT_GROUP=$(GROUP_NAME) \
-f $(DOCKERFILE) \
--target build \
--build-arg BUILDKIT_INLINE_CACHE=1 \
-t $(DOCKER_BUILD_IMAGE) $(MAKEFILE_DIR)

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force
