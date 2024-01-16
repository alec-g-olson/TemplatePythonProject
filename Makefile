MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYPROJECT_TOML = $(MAKEFILE_DIR)pyproject.toml
VERSION = $(shell awk -F'[ ="]+' '$$1 == "version" { print $$2 }' $(PYPROJECT_TOML))
PROJECT_NAME = $(shell awk -F'[ ="]+' '$$1 == "name" { print $$2 }' $(PYPROJECT_TOML))
BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
USER_ID = $(shell id -u)
USER_GROUP = $(shell id -g)

BUILD_DIR = $(MAKEFILE_DIR)build
BUILD_SUPPORT_DIR = $(MAKEFILE_DIR)build_support
DIST_DIR = $(BUILD_DIR)/dist

GIT_DATA_FILE = $(BUILD_DIR)/git_info.json

DOCKER_DEV_IMAGE = $(PROJECT_NAME):dev
DOCKER_PROD_IMAGE = $(PROJECT_NAME):prod
DOCKER_CONTEXT = $(MAKEFILE_DIR)
ifdef DOCKER_CONFIG_DIR
DOCKER_CONFIG_ARG = --config $(DOCKER_CONFIG_DIR)
else ifdef HOME
DOCKER_CONFIG_ARG = --config $(HOME)/.docker
endif
# How to deal with caching
ifeq ($(CACHE_TYPE), NONE)
  DOCKER_DEV_CACHE_ARG = --no-cache
  DOCKER_PROD_CACHE_ARG = --no-cache
else
  DOCKER_DEV_CACHE_ARG = --cache-from $(DOCKER_DEV_IMAGE)
  DOCKER_PROD_CACHE_ARG = --cache-from $(DOCKER_PROD_IMAGE)
endif

HTML_REPORT_NAME = $(PROJECT_NAME)_test_report_$(VERSION).html
HTML_REPORT = $(BUILD_DIR)/$(HTML_REPORT_NAME)
XML_REPORT_NAME = $(PROJECT_NAME)_test_report_$(VERSION).xml
XML_REPORT = $(BUILD_DIR)/$(XML_REPORT_NAME)
COVERAGE_XML_REPORT_NAME = $(PROJECT_NAME)_coverage_report_$(VERSION).xml
COVERAGE_XML_REPORT = $(BUILD_DIR)/$(COVERAGE_XML_REPORT_NAME)
COVERAGE_HTML_REPORT_NAME = $(PROJECT_NAME)_coverage_report_$(VERSION)
COVERAGE_HTML_REPORT = $(BUILD_DIR)/$(COVERAGE_HTML_REPORT_NAME)
TEST_ARGS = --cov-report term-missing --cov-report xml:build/$(COVERAGE_XML_REPORT_NAME) --cov-report html:build/$(COVERAGE_HTML_REPORT_NAME) --cov=. --junitxml=build/$(XML_REPORT_NAME) --html=build/$(HTML_REPORT_NAME) --self-contained-html


DOCKER_REMOTE_DEV_ROOT = /usr/dev
DOCKER_REMOTE_BUILD_SUPPORT = $(DOCKER_REMOTE_DEV_ROOT)/build_support
DOCKER_REMOTE_SRC = $(DOCKER_REMOTE_DEV_ROOT)/src
DOCKER_REMOTE_TEST = $(DOCKER_REMOTE_DEV_ROOT)/test
DOCKER_REMOTE_SRC_AND_TEST = $(DOCKER_REMOTE_SRC) $(DOCKER_REMOTE_TEST)
DOCKER_REMOTE_ALL_PYTHON_FOLDERS = $(DOCKER_REMOTE_SRC_AND_TEST) $(DOCKER_REMOTE_BUILD_SUPPORT)
DOCKER_REMOTE_BUILD = $(DOCKER_REMOTE_DEV_ROOT)/build
DOCKER_REMOTE_TEMP_DIST = $(DOCKER_REMOTE_DEV_ROOT)/dist
DOCKER_REMOTE_DIST = $(DOCKER_REMOTE_BUILD)/dist

BASE_DOCKER_COMMAND = docker run --rm --workdir=$(DOCKER_REMOTE_DEV_ROOT) -e "PYTHONPATH=$(DOCKER_REMOTE_SRC):$(DOCKER_REMOTE_TEST)" -v $(MAKEFILE_DIR):$(DOCKER_REMOTE_DEV_ROOT)
DOCKER_COMMAND = $(BASE_DOCKER_COMMAND) --user $(USER_ID):$(USER_GROUP) $(DOCKER_DEV_IMAGE)
INTERACTIVE_DOCKER_COMMAND = $(BASE_DOCKER_COMMAND) -it $(DOCKER_DEV_IMAGE)

PROD_DOCKER_COMMAND = $(BASE_DOCKER_COMMAND) $(DOCKER_PROD_IMAGE)
INTERACTIVE_PROD_DOCKER_COMMAND = $(BASE_DOCKER_COMMAND) -it $(DOCKER_PROD_IMAGE)





.PHONY: all
all: docker_prune_all clean lint autoflake build_artifact push


.PHONY: push
push:
	python3 $(BUILD_SUPPORT_DIR)/push_if_allowed.py

.PHONY: build_artifact
build_artifact: test build_prod_environment
	rm -rf $(DIST_DIR) # cleans the dist dir before building new dist
	$(PROD_DOCKER_COMMAND) poetry build
	# This can get cleaned up once a new version of poetry supporting "-o" is released
	$(PROD_DOCKER_COMMAND) mv $(DOCKER_REMOTE_TEMP_DIST) $(DOCKER_REMOTE_DIST)
	$(PROD_DOCKER_COMMAND) chown -R $(USER_ID):$(USER_GROUP) $(DOCKER_REMOTE_DIST)

.PHONY: test
test: test_without_style
	$(DOCKER_COMMAND) isort --check-only $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)
	$(DOCKER_COMMAND) black --check $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)
	$(DOCKER_COMMAND) pydocstyle $(DOCKER_REMOTE_SRC) $(DOCKER_REMOTE_BUILD_SUPPORT)
	$(DOCKER_COMMAND) pydocstyle --add-ignore=D100,D104 $(DOCKER_REMOTE_TEST)
	$(DOCKER_COMMAND) flake8 $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)
	$(DOCKER_COMMAND) mypy $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)

.PHONY: autoflake
autoflake: lint test_without_style  # Do not autoflake unless tests are passing - can rewrite bad code in cascading ways
	$(DOCKER_COMMAND) autoflake --remove-all-unused-imports --remove-duplicate-keys --in-place --recursive $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)

.PHONY: lint
lint: build_dev_environment
	$(DOCKER_COMMAND) isort $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)
	$(DOCKER_COMMAND) black $(DOCKER_REMOTE_ALL_PYTHON_FOLDERS)

.PHONY: test_without_style
test_without_style: build_dev_environment get_git_info
	$(eval THREADS := $(shell docker run --rm $(DOCKER_DEV_IMAGE) python -c "import multiprocessing;print(multiprocessing.cpu_count())"))
	$(DOCKER_COMMAND) pytest -n $(THREADS) $(TEST_ARGS) $(DOCKER_REMOTE_SRC_AND_TEST)

.PHONY: open_docker_shell
open_docker_shell: build_dev_environment
	$(INTERACTIVE_DOCKER_COMMAND) /bin/bash


.PHONY: build_dev_environment
build_dev_environment:
	$(DOCKER_LOGIN)
	#DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_DEV_CACHE_ARG) --target dev --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_DEV_IMAGE)" --secret id=pip.conf,src=$(PIP_CONF) $(DOCKER_CONTEXT)
	DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_DEV_CACHE_ARG) --target dev --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_DEV_IMAGE)" $(DOCKER_CONTEXT)

.PHONY: build_prod_environment
build_prod_environment:
	$(DOCKER_LOGIN)
	#DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_PROD_CACHE_ARG) --target prod --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_PROD_IMAGE)" --secret id=pip.conf,src=$(PIP_CONF) $(DOCKER_CONTEXT)
	DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_PROD_CACHE_ARG) --target prod --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_PROD_IMAGE)" $(DOCKER_CONTEXT)

.PHONY: get_git_info
get_git_info:
	mkdir -p $(BUILD_DIR)
	git fetch
	$(eval TAGS := $(shell git tag | awk '{ print "\""$$0"\""}'| tr '\n' ',' | awk '{ print substr( $$0, 1, length($$0)-1 ) }'))
	echo '{"branch": "$(BRANCH)", "tags": [$(TAGS)]}' > $(GIT_DATA_FILE)

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force
