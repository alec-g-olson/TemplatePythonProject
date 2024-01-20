"""Module for implementing PyPi domain specific tasks."""
from build_tasks.common_build_tasks import (
    BuildDevEnvironment,
    BuildProdEnvironment,
    PushTags,
    TestPythonStyle,
)
from common_vars import (
    BUILD_DIR,
    DIST_DIR,
    DOCKER_COMMAND,
    DOCKER_REMOTE_DIST,
    DOCKER_REMOTE_PYPI_SRC_AND_TEST,
    DOCKER_REMOTE_TEMP_DIST,
    PROD_DOCKER_COMMAND,
    PROJECT_NAME,
    THREADS_AVAILABLE,
    USER,
    VERSION,
)
from dag_engine import TaskNode, concatenate_args, run_process

HTML_REPORT_NAME = f"{PROJECT_NAME}_test_report_{VERSION}.html"
HTML_REPORT = BUILD_DIR.joinpath(HTML_REPORT_NAME)
XML_REPORT_NAME = f"{PROJECT_NAME}_test_report_{VERSION}.xml"
XML_REPORT = BUILD_DIR.joinpath(XML_REPORT_NAME)
COVERAGE_XML_REPORT_NAME = f"{PROJECT_NAME}_coverage_report_{VERSION}.xml"
COVERAGE_XML_REPORT = BUILD_DIR.joinpath(COVERAGE_XML_REPORT_NAME)
COVERAGE_HTML_REPORT_NAME = f"{PROJECT_NAME}_coverage_report_{VERSION}"
COVERAGE_HTML_REPORT = BUILD_DIR.joinpath(COVERAGE_HTML_REPORT_NAME)
TEST_REPORT_ARGS = [
    "--cov-report",
    "term-missing",
    "--cov-report",
    f"xml:build/{COVERAGE_XML_REPORT_NAME}",
    "--cov-report",
    f"html:build/{COVERAGE_HTML_REPORT_NAME}",
    "--cov=.",
    f"--junitxml=build/{XML_REPORT_NAME}",
    f"--html=build/{HTML_REPORT_NAME}",
    "--self-contained-html",
]


class TestPypi(TaskNode):
    """Task for testing PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Ensures dev env is built."""
        return [BuildDevEnvironment()]

    def run(self) -> None:
        """Tests the PyPi package."""
        run_process(
            args=concatenate_args(
                args=[
                    DOCKER_COMMAND,
                    "pytest",
                    "-n",
                    THREADS_AVAILABLE,
                    TEST_REPORT_ARGS,
                    DOCKER_REMOTE_PYPI_SRC_AND_TEST,
                ]
            )
        )


class BuildPypi(TaskNode):
    """Task for building PyPi package."""

    def required_tasks(self) -> list[TaskNode]:
        """Makes sure all python checks are passing and prod env exists."""
        return [
            TestPypi(),
            TestPythonStyle(),
            BuildProdEnvironment(),
        ]

    def run(self) -> None:
        """Builds PyPi package."""
        run_process(args=concatenate_args(args=["rm", "-rf", DIST_DIR]))
        run_process(
            args=concatenate_args(args=[PROD_DOCKER_COMMAND, "poetry", "build"])
        )
        # Todo: clean this up once a new version of poetry supporting "-o" is released
        run_process(
            args=concatenate_args(
                args=[
                    PROD_DOCKER_COMMAND,
                    "mv",
                    DOCKER_REMOTE_TEMP_DIST,
                    DOCKER_REMOTE_DIST,
                ]
            )
        )
        run_process(
            args=concatenate_args(
                args=[PROD_DOCKER_COMMAND, "chown", "-R", USER, DOCKER_REMOTE_DIST]
            )
        )


class PushPypi(TaskNode):
    """Pushes the PyPi package.  Will move to combined once a repo is managed in Pulumi."""

    def required_tasks(self) -> list[TaskNode]:
        """Must build PyPi and push git tags before PyPi is pushed."""
        return [PushTags(), BuildPypi()]

    def run(self) -> None:
        """Push PyPi."""
