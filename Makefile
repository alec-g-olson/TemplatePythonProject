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
USER = $(USER_ID):$(USER_GROUP)


BUILD_SUPPORT_COMMAND = docker run --rm --workdir=$(DOCKER_REMOTE_PROJECT_ROOT) \
-e PYTHONPATH=/usr/dev/build_support/build_src \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $(MAKEFILE_DIR):$(DOCKER_REMOTE_PROJECT_ROOT) \
$(DOCKER_BUILD_IMAGE) \
python build_support/build_src/build_tools.py \
--non-docker-project-root $(MAKEFILE_DIR)  --docker-project-root $(DOCKER_REMOTE_PROJECT_ROOT) \
--user-id $(USER_ID) --group-id $(USER_GROUP)

.PHONY: push
push: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) push

.PHONY: push_pypi
push_pypi: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) push_pypi

.PHONY: build_pypi
build_pypi: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) build_pypi

.PHONY: test
test: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) test

.PHONY: autoflake
autoflake: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) autoflake

.PHONY: lint
lint: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) lint

.PHONY: test_without_style
test_without_style: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) test_without_style

.PHONY: open_dev_docker_shell
open_dev_docker_shell: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) open_dev_docker_shell

.PHONY: open_prod_docker_shell
open_prod_docker_shell: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) open_prod_docker_shell

.PHONY: open_pulumi_docker_shell
open_pulumi_docker_shell: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) open_pulumi_docker_shell

.PHONY: clean
clean: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) clean

.PHONY: make_new_project
make_new_project: setup_build_envs
	$(BUILD_SUPPORT_COMMAND) make_new_project

.PHONY: setup_build_envs
setup_build_envs:
	docker login
	docker build -f $(DOCKERFILE) --target build --build-arg BUILDKIT_INLINE_CACHE=1 -t $(DOCKER_BUILD_IMAGE) $(MAKEFILE_DIR)

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force
