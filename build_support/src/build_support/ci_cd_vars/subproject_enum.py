from enum import Enum


class SubprojectContext(Enum):
    """An Enum to track the possible docker targets and images."""

    PYPI = "pypi_package"
    BUILD_SUPPORT = "build_support"
    PULUMI = "pulumi"
    DOCUMENTATION_ENFORCEMENT = "process_and_style_enforcement"
    ALL = "all"
