"""A configuration file for sphinx doc generation."""

from pathlib import Path

from build_support.ci_cd_vars.project_setting_vars import (
    get_project_name,
    get_project_version,
    get_pyproject_toml_data,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent


project = get_project_name(project_root=PROJECT_ROOT)
author = ", ".join(
    get_pyproject_toml_data(project_root=PROJECT_ROOT)["tool"]["poetry"]["authors"]
)
release = get_project_version(project_root=PROJECT_ROOT)
version = release


html_theme = "sphinx_rtd_theme"

# These folders are copied to the documentation's HTML output (docs/build)
# Note: These are relative to the sphinx configuration directory
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
