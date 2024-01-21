MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

BUILD_SUPPORT_COMMAND = PYTHONPATH=$(MAKEFILE_DIR)build_support/build_src python build_support/build_src/build_tools.py

.PHONY: push
push:
	$(BUILD_SUPPORT_COMMAND) push

.PHONY: push_pypi
push_pypi:
	$(BUILD_SUPPORT_COMMAND) push_pypi

.PHONY: build_pypi
build_pypi:
	$(BUILD_SUPPORT_COMMAND) build_pypi

.PHONY: test
test:
	$(BUILD_SUPPORT_COMMAND) test

.PHONY: autoflake
autoflake:
	$(BUILD_SUPPORT_COMMAND) autoflake

.PHONY: lint
lint:
	$(BUILD_SUPPORT_COMMAND) lint

.PHONY: test_without_style
test_without_style:
	$(BUILD_SUPPORT_COMMAND) test_without_style

.PHONY: open_dev_docker_shell
open_dev_docker_shell:
	$(BUILD_SUPPORT_COMMAND) open_dev_docker_shell

.PHONY: open_prod_docker_shell
open_prod_docker_shell:
	$(BUILD_SUPPORT_COMMAND) open_prod_docker_shell

.PHONY: open_pulumi_docker_shell
open_pulumi_docker_shell:
	$(BUILD_SUPPORT_COMMAND) open_pulumi_docker_shell

.PHONY: clean
clean:
	$(BUILD_SUPPORT_COMMAND) clean

.PHONY: docker_prune_all
docker_prune_all:
	$(BUILD_SUPPORT_COMMAND) docker_prune_all

.PHONY: make_new_project
make_new_project:
	$(BUILD_SUPPORT_COMMAND) make_new_project
