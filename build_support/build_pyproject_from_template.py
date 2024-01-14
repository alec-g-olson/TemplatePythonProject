import sys
from pathlib import Path
from typing import List


def get_variables_and_values(args: List[str]):
    """Get variables and values from the command line."""
    variables_to_assign = {}
    for arg in args:
        variable, value = arg.split("=")
        variables_to_assign[variable] = value
    return variables_to_assign


def get_dependencies(template_file: Path) -> str:
    """Get the current version of each dependency in requirements.in.

    These values are retrieved from requirements.txt.
    """
    requirements_txt = template_file.parent.joinpath("requirements.txt")
    package_to_version = {}
    for line in requirements_txt.open():
        line = line.rstrip()
        if "==" in line:
            package, version = line.split("==")
            package_to_version[package] = version
    requirements_in = template_file.parent.joinpath("requirements.in")
    dependencies = []
    for line in requirements_in.open():
        line = line.rstrip()
        dependencies.append("'" + line + ">=" + package_to_version[line] + "'")
    return "  " + ",\n  ".join(dependencies)


def main(args: List[str]):
    """Run this program.

    In reality this is a "sub-main" method that we broke out.
    """
    template_file = Path(args[1])
    output_file = template_file.parent.joinpath(template_file.name[0:-4])
    variables_to_assign = get_variables_and_values(args=args[2:])
    variables_to_assign["DEPENDENCIES"] = get_dependencies(template_file=template_file)
    file_contents = template_file.read_text()
    for variable, value in variables_to_assign.items():
        file_contents = file_contents.replace("{{" + variable + "}}", value)
    output_file.write_text(file_contents)


if __name__ == "__main__":  # pragma: no cover
    main(args=sys.argv)
