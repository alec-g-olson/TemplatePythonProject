"""A place to hold tasks and variable used in multiple domains."""
import multiprocessing
import tomllib
from pathlib import Path

from dag_engine import concatenate_args, get_output_of_process

PROJECT_ROOT_DIR = Path(__file__).parent.parent.parent
PYPROJECT_TOML = PROJECT_ROOT_DIR.joinpath("pyproject.toml")
PROJECT_SETTINGS_TOML = PROJECT_ROOT_DIR.joinpath(
    "build_support", "project_settings.json"
)


PYPROJECT_TOML_DATA = tomllib.loads(PYPROJECT_TOML.read_text())
VERSION = "v" + PYPROJECT_TOML_DATA["tool"]["poetry"]["version"]
PROJECT_NAME = PYPROJECT_TOML_DATA["tool"]["poetry"]["name"]
BRANCH = get_output_of_process(
    args=["git", "rev-parse", "--abbrev-ref", "HEAD"], silent=True
)
USER_ID = get_output_of_process(args=["id", "-u"], silent=True)
USER_GROUP = get_output_of_process(args=["id", "-g"], silent=True)
USER = ":".join([USER_ID, USER_GROUP])


BUILD_DIR = PROJECT_ROOT_DIR.joinpath("build")
BUILD_SUPPORT_DIR = PROJECT_ROOT_DIR.joinpath("build_support")
DIST_DIR = BUILD_DIR.joinpath("dist")

GIT_DATA_FILE = BUILD_DIR.joinpath("git_info.json")

DOCKER_DEV_IMAGE = ":".join([PROJECT_NAME, "dev"])
DOCKER_PROD_IMAGE = ":".join([PROJECT_NAME, "prod"])
DOCKER_PULUMI_IMAGE = ":".join([PROJECT_NAME, "pulumi"])
DOCKER_CONTEXT = PROJECT_ROOT_DIR
DOCKERFILE = PROJECT_ROOT_DIR.joinpath("Dockerfile")

DOCKER_REMOTE_DEV_ROOT = Path("/usr/dev")
DOCKER_REMOTE_BUILD_SUPPORT = DOCKER_REMOTE_DEV_ROOT.joinpath("build_support")
DOCKER_REMOTE_BUILD_SUPPORT_SRC = DOCKER_REMOTE_BUILD_SUPPORT.joinpath("build_src")
DOCKER_REMOTE_BUILD_SUPPORT_TESTS = DOCKER_REMOTE_BUILD_SUPPORT.joinpath("build_test")
DOCKER_REMOTE_BUILD_SUPPORT_SRC_AND_TEST = [
    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
]
DOCKER_REMOTE_PYPI_SRC = DOCKER_REMOTE_DEV_ROOT.joinpath("src")
DOCKER_REMOTE_PYPI_TEST = DOCKER_REMOTE_DEV_ROOT.joinpath("test")
DOCKER_REMOTE_PULUMI = DOCKER_REMOTE_DEV_ROOT.joinpath("pulumi")
DOCKER_REMOTE_PYPI_SRC_AND_TEST = [DOCKER_REMOTE_PYPI_SRC, DOCKER_REMOTE_PYPI_TEST]
DOCKER_REMOTE_DEV = [
    DOCKER_REMOTE_PYPI_SRC,
    DOCKER_REMOTE_PYPI_TEST,
    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
]
DOCKER_REMOTE_ALL_PYTHON_FOLDERS = [
    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
    DOCKER_REMOTE_PYPI_SRC,
    DOCKER_REMOTE_PYPI_TEST,
    DOCKER_REMOTE_PULUMI,
]
DOCKER_REMOTE_ALL_SRC_FOLDERS = [
    DOCKER_REMOTE_BUILD_SUPPORT_SRC,
    DOCKER_REMOTE_PYPI_SRC,
    DOCKER_REMOTE_PULUMI,
]
DOCKER_REMOTE_ALL_TEST_FOLDERS = [
    DOCKER_REMOTE_BUILD_SUPPORT_TESTS,
    DOCKER_REMOTE_PYPI_TEST,
]
DOCKER_REMOTE_BUILD = DOCKER_REMOTE_DEV_ROOT.joinpath("build")
DOCKER_REMOTE_TEMP_DIST = DOCKER_REMOTE_DEV_ROOT.joinpath("dist")
DOCKER_REMOTE_DIST = DOCKER_REMOTE_BUILD.joinpath("dist")

PYTHON_PATH_TO_INCLUDE = ":".join(str(x) for x in DOCKER_REMOTE_DEV)

BASE_DOCKER_COMMAND = [
    "docker",
    "run",
    "--rm",
    f"--workdir={DOCKER_REMOTE_DEV_ROOT}",
    "-e",
    "PYTHONPATH=" + PYTHON_PATH_TO_INCLUDE,
    "-v",
    f"{PROJECT_ROOT_DIR}:{DOCKER_REMOTE_DEV_ROOT}",
]
DOCKER_COMMAND = concatenate_args(
    [BASE_DOCKER_COMMAND, "--user", USER, DOCKER_DEV_IMAGE]
)
INTERACTIVE_DOCKER_COMMAND = concatenate_args(
    [BASE_DOCKER_COMMAND, "-it", DOCKER_DEV_IMAGE]
)

PROD_DOCKER_COMMAND = concatenate_args([BASE_DOCKER_COMMAND, DOCKER_PROD_IMAGE])
INTERACTIVE_PROD_DOCKER_COMMAND = concatenate_args(
    [BASE_DOCKER_COMMAND, "-it", DOCKER_PROD_IMAGE]
)


BASE_PULUMI_DOCKER_COMMAND = [
    "docker",
    "run",
    "--rm",
    f"--workdir={DOCKER_REMOTE_DEV_ROOT}",
    "-e",
    f"PYTHONPATH={DOCKER_REMOTE_PYPI_SRC}:{DOCKER_REMOTE_PYPI_TEST}:{DOCKER_REMOTE_BUILD_SUPPORT}",
    "-v",
    f"{PROJECT_ROOT_DIR}:{DOCKER_REMOTE_DEV_ROOT}",
]
PULUMI_DOCKER_COMMAND = concatenate_args(
    [BASE_PULUMI_DOCKER_COMMAND, "--user", USER, DOCKER_PULUMI_IMAGE]
)
INTERACTIVE_PULUMI_DOCKER_COMMAND = concatenate_args(
    [BASE_PULUMI_DOCKER_COMMAND, "-it", DOCKER_PULUMI_IMAGE]
)

THREADS_AVAILABLE = multiprocessing.cpu_count()

PUSH_ALLOWED = (BRANCH == "main") ^ ("dev" in VERSION)
