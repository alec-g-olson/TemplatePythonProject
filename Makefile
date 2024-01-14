MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VERSION = $(shell cat $(MAKEFILE_DIR)/semver)
USER_ID = $(shell id -u)
USER_GROUP = $(shell id -g)

PROJECT_NAME = template_python_project
BUILD_DIR = $(MAKEFILE_DIR)build
DIST_DIR = $(BUILD_DIR)/dist

GIT_DATA_FILE = $(BUILD_DIR)/git_info.json

DOCKER_DEV_IMAGE = $(PROJECT_NAME):dev
DOCKER_CONTEXT = $(MAKEFILE_DIR)
ifdef DOCKER_CONFIG_DIR
DOCKER_CONFIG_ARG = --config $(DOCKER_CONFIG_DIR)
else ifdef HOME
DOCKER_CONFIG_ARG = --config $(HOME)/.docker
endif
# How to deal with caching
ifeq ($(CACHE_TYPE), NONE)
  DOCKER_CACHE_ARG = --no-cache
else
  DOCKER_CACHE_ARG = --cache-from $(DOCKER_DEV_IMAGE)
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
DOCKER_REMOTE_SRC = $(DOCKER_REMOTE_DEV_ROOT)/src
DOCKER_REMOTE_TEST = $(DOCKER_REMOTE_DEV_ROOT)/test
DOCKER_REMOTE_SRC_AND_TEST = $(DOCKER_REMOTE_SRC) $(DOCKER_REMOTE_TEST)
DOCKER_REMOTE_BUILD = $(DOCKER_REMOTE_DEV_ROOT)/build
DOCKER_REMOTE_BUILD_SUPPORT = $(DOCKER_REMOTE_DEV_ROOT)/build_support
DOCKER_REMOTE_DIST = $(DOCKER_REMOTE_BUILD)/dist

DOCKER_REMOTE_FILES_TO_MAINTAIN = $(DOCKER_REMOTE_SRC_AND_TEST) $(DOCKER_REMOTE_BUILD_SUPPORT)

DOCKER_COMMAND = docker run --rm --workdir=$(DOCKER_REMOTE_DEV_ROOT) --user $(USER_ID):$(USER_GROUP) -e "PYTHONPATH=$(DOCKER_REMOTE_SRC):$(DOCKER_REMOTE_TEST)" -v $(MAKEFILE_DIR):$(DOCKER_REMOTE_DEV_ROOT) $(DOCKER_DEV_IMAGE)
DOCKER_BUILD_SUPPORT = $(DOCKER_REMOTE_DEV_ROOT)/build_support


.PHONY: all
all: docker_prune_all clean lint autoflake build_artifact push

.PHONY: push
push: build_artifact

.PHONY: build_artifact
build_artifact: test
	rm -rf $(DIST_DIR) # cleans the dist dir before building new dist
	$(DOCKER_COMMAND) python3 -m build -o $(DOCKER_REMOTE_DIST)

.PHONY: test
test: test_without_style
	$(DOCKER_COMMAND) isort --check-only $(DOCKER_REMOTE_FILES_TO_MAINTAIN)
	$(DOCKER_COMMAND) black --check $(DOCKER_REMOTE_FILES_TO_MAINTAIN)
	$(DOCKER_COMMAND) pydocstyle $(DOCKER_REMOTE_SRC)
	$(DOCKER_COMMAND) pydocstyle --add-ignore=D100,D104 $(DOCKER_REMOTE_TEST) $(DOCKER_REMOTE_BUILD_SUPPORT)
	$(DOCKER_COMMAND) flake8 $(DOCKER_REMOTE_FILES_TO_MAINTAIN)
	$(DOCKER_COMMAND) mypy $(DOCKER_REMOTE_FILES_TO_MAINTAIN)

.PHONY: autoflake
autoflake: lint test_without_style  # Do not autoflake unless tests are passing - can cause cascading issues
	$(DOCKER_COMMAND) autoflake --remove-all-unused-imports --remove-duplicate-keys --in-place --recursive $(DOCKER_REMOTE_SRC_AND_TEST)

.PHONY: lint
lint: build_dev_environment
	$(DOCKER_COMMAND) isort $(DOCKER_REMOTE_FILES_TO_MAINTAIN)
	$(DOCKER_COMMAND) black $(DOCKER_REMOTE_FILES_TO_MAINTAIN)

.PHONY: test_without_style
test_without_style: build_pyproject_toml
	$(eval THREADS := $(shell docker run --rm $(DOCKER_DEV_IMAGE) python -c "import multiprocessing;print(multiprocessing.cpu_count())"))
	$(DOCKER_COMMAND) pytest -n $(THREADS) $(TEST_ARGS) $(DOCKER_REMOTE_SRC_AND_TEST)

.PHONY: build_pyproject_toml
build_pyproject_toml: build_dev_environment get_git_info
	$(DOCKER_COMMAND) python3 $(DOCKER_BUILD_SUPPORT)/build_pyproject_from_template.py $(DOCKER_REMOTE_DEV_ROOT)/pyproject.toml.tmp PACKAGE_NAME=$(PROJECT_NAME) PACKAGE_VERSION=$(VERSION)

.PHONY: build_dev_environment
build_dev_environment:
	$(DOCKER_LOGIN)
	#DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_CACHE_ARG) --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_DEV_IMAGE)" --secret id=pip.conf,src=$(PIP_CONF) $(DOCKER_CONTEXT)
	DOCKER_BUILDKIT=1 docker $(DOCKER_CONFIG_ARG) build $(DOCKER_CACHE_ARG) --build-arg BUILDKIT_INLINE_CACHE=1 -t "$(DOCKER_DEV_IMAGE)" $(DOCKER_CONTEXT)
	docker run --rm "$(DOCKER_DEV_IMAGE)" cat requirements.txt > requirements.txt

.PHONY: get_git_info
get_git_info:
	mkdir -p $(BUILD_DIR)
	$(eval BRANCH := $(shell git rev-parse --abbrev-ref HEAD))
	echo '{"branch": "$(BRANCH)"}' > $(GIT_DATA_FILE)

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR) $(MAKEFILE_DIR)pyproject.toml

.PHONY: docker_prune_all
docker_prune_all:
	docker ps -q | xargs -r docker stop
	docker system prune --all --force
