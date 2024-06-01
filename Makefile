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

NON_DOCKER_ROOT = $(MAKEFILE_DIR)

CI_CD_INTEGRATION_TEST_MODE_FLAG =

USER_HOME_DIR = ${HOME}
GIT_CONFIG_PATH = $(USER_HOME_DIR)/.gitconfig

ifneq ("$(wildcard $(GIT_CONFIG_PATH))","")
	# If there is a .gitconfig file, mount it (there isn't one on GitHub)
	# Don't override GIT_MOUNT if set from command line
	GIT_MOUNT ?= -v ~/.ssh:/home/$(USER_NAME)/.ssh:ro -v ~/.gitconfig:/home/$(USER_NAME)/.gitconfig
else
	# If no .gitconfig, don't mount it
	# Don't override GIT_MOUNT if set from command line
	GIT_MOUNT ?= -v ~/.ssh:/home/$(USER_NAME)/.ssh:ro
endif

BASE_DOCKER_BUILD_ENV_COMMAND = docker run --rm \
--workdir=$(DOCKER_REMOTE_PROJECT_ROOT) \
-e PYTHONPATH=/usr/dev/build_support/src \
$(GIT_MOUNT) \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $(NON_DOCKER_ROOT):$(DOCKER_REMOTE_PROJECT_ROOT)

DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) $(DOCKER_BUILD_IMAGE)
INTERACTIVE_DOCKER_BUILD_ENV_COMMAND = $(BASE_DOCKER_BUILD_ENV_COMMAND) \
-it $(DOCKER_BUILD_IMAGE)

SHARED_BUILD_VARS = --docker-project-root $(DOCKER_REMOTE_PROJECT_ROOT)

EXECUTE_BUILD_STEPS_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) \
python build_support/src/build_support/execute_build_steps.py \
$(SHARED_BUILD_VARS)

GET_BUILD_VAR_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) \
python build_support/src/build_support/report_build_var.py \
--non-docker-project-root $(NON_DOCKER_ROOT) \
$(SHARED_BUILD_VARS) --build-variable-to-report

DUMP_RUN_INFO_COMMAND = $(DOCKER_BUILD_ENV_COMMAND) \
python build_support/src/build_support/dump_ci_cd_run_info.py \
--user-id $(USER_ID) --group-id $(GROUP_ID) \
--non-docker-project-root $(NON_DOCKER_ROOT) \
$(SHARED_BUILD_VARS) \
$(CI_CD_INTEGRATION_TEST_MODE_FLAG)

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

.PHONY: lint_apply_unsafe_fixes
lint_apply_unsafe_fixes: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) lint_apply_unsafe_fixes

.PHONY: format
format: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) format

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

.PHONY: type_checks
type_checks: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) type_checks

.PHONY: security_checks
security_checks: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) security_checks

.PHONY: check_process
check_process: setup_build_env
	$(EXECUTE_BUILD_STEPS_COMMAND) check_process

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
ifeq ($(CI_CD_INTEGRATION_TEST_MODE_FLAG), )
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
else
	echo "Skipping building build docker image in CI/CD mode."
endif
	$(DUMP_RUN_INFO_COMMAND)

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force

.PHONY: echo_v
echo_v:
	echo $(BASE_DOCKER_BUILD_ENV_COMMAND)
