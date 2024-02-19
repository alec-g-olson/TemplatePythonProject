from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from re import compile
from textwrap import dedent
from typing import Any

import pytest
from pydocstyle import ConventionChecker
from pydocstyle.parser import Class, Function, Method, Module, Package, Parser

sub_projects_to_enforce_docstrings = ["pypi_package"]  # , "build_support"]


@pytest.fixture(params=sub_projects_to_enforce_docstrings)
def package_to_test(real_project_root_dir: Path, request) -> Path:
    return real_project_root_dir.joinpath(request.param, "src")


def get_all_module_paths_in(top_package: Path, all_modules: list[Path]) -> None:
    sub_folders = []
    python_modules = []
    for path in top_package.glob("*"):
        if path.is_dir():
            sub_folders.append(path)
        elif path.name.endswith(".py"):
            python_modules.append(path)
    all_modules += sorted(python_modules)
    for sub_folder in sorted(sub_folders):
        get_all_module_paths_in(top_package=sub_folder, all_modules=all_modules)


def get_all_module_paths(top_package: Path) -> list[Path]:
    all_modules_to_test = []
    get_all_module_paths_in(top_package=top_package, all_modules=all_modules_to_test)
    return all_modules_to_test


def get_flattened_public_children(element_to_flatten: Any) -> list[Any]:
    flattened_list = [element_to_flatten]
    for child in element_to_flatten.children:
        if child.is_public:  # pragma: no cover - branching, all could be public
            flattened_list += get_flattened_public_children(element_to_flatten=child)
    return flattened_list


def parse_all_objects(package_to_test: Path) -> list[Any]:
    all_modules_to_test = get_all_module_paths(top_package=package_to_test)
    pydocstyle_parser = Parser()
    all_objects = []
    for module_path in all_modules_to_test:
        parsed_module = pydocstyle_parser.parse(
            filelike=module_path.open(),
            filename=str(module_path.relative_to(package_to_test)),
        )
        all_objects += get_flattened_public_children(element_to_flatten=parsed_module)
    return all_objects


def get_all_packages_in(package_to_test: Path) -> list[Package]:
    return [
        obj
        for obj in parse_all_objects(package_to_test=package_to_test)
        if isinstance(obj, Package)
    ]


def get_all_modules_in(package_to_test: Path) -> list[Module]:
    return [
        obj
        for obj in parse_all_objects(package_to_test=package_to_test)
        if isinstance(obj, Module) and not isinstance(obj, Package)
    ]


def get_all_classes_in(package_to_test: Path) -> list[Class]:
    return [
        obj
        for obj in parse_all_objects(package_to_test=package_to_test)
        if isinstance(obj, Class)
    ]


def get_all_functions_in(package_to_test: Path) -> list[Function]:
    return [
        obj
        for obj in parse_all_objects(package_to_test=package_to_test)
        if isinstance(obj, Function) and not isinstance(obj, Method)
    ]


def get_all_methods_in(package_to_test: Path) -> list[Method]:
    return [
        obj
        for obj in parse_all_objects(package_to_test=package_to_test)
        if isinstance(obj, Method)
    ]


def get_source_file_name(
    parsed_element: Package | Module | Class | Function | Method,
) -> str:  # pragma: no cover if all pass
    if isinstance(parsed_element, (Package, Module)):
        return parsed_element.name
    else:
        return get_source_file_name(parsed_element=parsed_element.parent)


def get_element_name(
    parsed_element: Package | Module | Class | Function | Method,
    suffix_to_add: str | None = None,
) -> str:  # pragma: no cover if all pass
    if not suffix_to_add:
        suffix_to_add = ""
    if isinstance(parsed_element, (Package, Module)):
        return suffix_to_add
    else:
        if suffix_to_add:
            suffix_to_add = parsed_element.name + "." + suffix_to_add
        else:
            suffix_to_add = parsed_element.name
        return get_element_name(
            parsed_element=parsed_element.parent, suffix_to_add=suffix_to_add
        )


required_package_sections = ["Arguments", ["Returns", "Yields"]]
required_module_sections = ["Arguments", ["Returns", "Yields"]]
required_class_sections = ["Arguments", ["Returns", "Yields"]]
required_method_sections = ["Arguments", ["Returns", "Yields"]]

convention_checker = ConventionChecker()


def flatten_required_groups(sections_to_consider: list[str | list[str]]) -> list[str]:
    contexts = []
    for group in sections_to_consider:
        if isinstance(group, str):
            contexts.append(group)
        else:
            contexts += group
    return contexts


SectionContext = namedtuple(
    "SectionContext",
    (
        "section_name",
        "previous_line",
        "line",
        "following_lines",
        "original_index",
        "is_last_section",
    ),
)


def get_docstring_contexts(
    docstring: str, sections_to_consider: list[str]
) -> dict[str, SectionContext]:
    lines = docstring.split("\n")
    return {
        context.section_name: normalize_context(context=context)
        for context in convention_checker._get_section_contexts(
            lines, sections_to_consider
        )
    }


def normalize_context(context: SectionContext) -> SectionContext:
    if context.following_lines:  # pragma: no cover - all context might have lines
        first_line = context.following_lines[0]
        leading_whitespaces = first_line[: -len(first_line.lstrip())]

    args_content = dedent(
        "\n".join(
            [
                line
                for line in context.following_lines
                if line.startswith(leading_whitespaces) or line == ""
            ]
        )
    ).strip()
    return SectionContext(
        section_name=context.section_name,
        previous_line=context.previous_line,
        line=context.line,
        following_lines=args_content.splitlines(keepends=True),
        original_index=context.original_index,
        is_last_section=context.is_last_section,
    )


@dataclass
class PackageDocstringData:
    module_name: str
    missing_sections: list[str]
    extra_sub_packages: list[str]
    missing_sub_packages: list[str]
    extra_modules: list[str]
    missing_modules: list[str]


def test_all_package_docstrings(package_to_test: Path):
    for parsed_package in get_all_packages_in(package_to_test=package_to_test):
        print(get_source_file_name(parsed_element=parsed_package))
        print(get_element_name(parsed_element=parsed_package))


def test_all_module_docstrings(package_to_test: Path):
    for parsed_module in get_all_modules_in(package_to_test=package_to_test):
        print(get_source_file_name(parsed_element=parsed_module))
        print(get_element_name(parsed_element=parsed_module))


def test_all_class_docstrings(package_to_test: Path):
    for parsed_class in get_all_classes_in(package_to_test=package_to_test):
        print(get_source_file_name(parsed_element=parsed_class))
        print(get_element_name(parsed_element=parsed_class))


@dataclass
class FunctionDocstringData:
    module_name: str
    function_name: str
    missing_sections: list[str]
    arg_missing_type_or_description: list[str]
    extra_args: list[str]
    result_missing_type_or_description: bool


@dataclass
class MethodDocstringData(FunctionDocstringData):
    pass


LOOSE_GOOGLE_ARGS_REGEX = compile(r"^\s*(\w+)\s*(\(.*\))?\s*:.*")
ENFORCED_GOOGLE_ARGS_REGEX = compile(r"^\s*(\w+)\s*(\(.*\))\s*:\n?\s*.+")

GOOGLE_RESULT_REGEX = compile(r"^\s*((\w+)\s*:.*|None)")


def parse_arg_section(
    arg_section: str,
    contexts: dict[str, SectionContext],
    parsed_object: Any,
    missing_sections: list[str],
    args_missing_stuff: list[str],
    extra_args: list[str],
):
    args_to_consider = [
        arg for arg in parsed_object.callable_args if arg not in ["self", "cls"]
    ]
    if args_to_consider:
        if arg_section not in contexts:  # pragma: no cover if all pass
            missing_sections.append(arg_section)
        else:
            args_docs = []
            for line in contexts[arg_section].following_lines:
                if not line[:1].isspace():
                    args_docs.append(line)
                else:  # pragma: no cover if no multiline
                    args_docs[-1] += line
            for arg_doc in args_docs:
                match_result = LOOSE_GOOGLE_ARGS_REGEX.match(arg_doc)
                if match_result:  # pragma: no cover if all pass
                    arg = match_result.group(1)
                    if arg not in parsed_object.callable_args:
                        extra_args.append(arg)
                    elif not ENFORCED_GOOGLE_ARGS_REGEX.match(arg_doc):
                        args_missing_stuff.append(arg)


def get_missing_or_malformed_section_info(
    arg_section: str,
    res_sections: list[str],
    parsed_object: Any,
    contexts: dict[str, SectionContext],
) -> tuple[list[str], list[str], list[str], bool]:
    missing_sections = []
    args_missing_stuff = []
    extra_args = []
    parse_arg_section(
        arg_section=arg_section,
        contexts=contexts,
        parsed_object=parsed_object,
        missing_sections=missing_sections,
        args_missing_stuff=args_missing_stuff,
        extra_args=extra_args,
    )
    found_result = False
    result_badly_formatted = True
    for result in res_sections:
        if result in contexts:
            found_result = True
            result_match = GOOGLE_RESULT_REGEX.match(
                contexts[result].following_lines[0]
            )
            if result_match:  # pragma: no cover if all pass
                result_badly_formatted = False
    if not found_result:  # pragma: no cover if all pass
        missing_sections.append("|".join(res_sections))
    return missing_sections, args_missing_stuff, extra_args, result_badly_formatted


def test_all_method_docstrings(package_to_test: Path):
    method_with_issues_in_docstrings = []
    arguments_section = "Arguments"
    possible_result_section = ["Returns", "Yields"]
    for parsed_method in get_all_methods_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(
            docstring=parsed_method.docstring,
            sections_to_consider=flatten_required_groups(
                sections_to_consider=[arguments_section, possible_result_section]
            ),
        )
        (
            missing_sections,
            args_missing_stuff,
            extra_args,
            result_badly_formatted,
        ) = get_missing_or_malformed_section_info(
            arg_section=arguments_section,
            res_sections=possible_result_section,
            parsed_object=parsed_method,
            contexts=contexts,
        )
        if (
            missing_sections
            or args_missing_stuff
            or extra_args
            or result_badly_formatted
        ):  # pragma: no cover if all pass
            method_with_issues_in_docstrings.append(
                MethodDocstringData(
                    module_name=get_source_file_name(parsed_element=parsed_method),
                    function_name=get_element_name(parsed_element=parsed_method),
                    missing_sections=missing_sections,
                    arg_missing_type_or_description=args_missing_stuff,
                    extra_args=extra_args,
                    result_missing_type_or_description=result_badly_formatted,
                )
            )

    assert method_with_issues_in_docstrings == []


def test_all_function_docstrings(package_to_test: Path):
    functions_with_issues_in_docstrings = []
    arguments_section = "Arguments"
    possible_result_section = ["Returns", "Yields"]
    for parsed_function in get_all_functions_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(
            docstring=parsed_function.docstring,
            sections_to_consider=flatten_required_groups(
                sections_to_consider=[arguments_section, possible_result_section]
            ),
        )
        (
            missing_sections,
            args_missing_stuff,
            extra_args,
            result_badly_formatted,
        ) = get_missing_or_malformed_section_info(
            arg_section=arguments_section,
            res_sections=possible_result_section,
            parsed_object=parsed_function,
            contexts=contexts,
        )
        if (
            missing_sections
            or args_missing_stuff
            or extra_args
            or result_badly_formatted
        ):  # pragma: no cover if all pass
            functions_with_issues_in_docstrings.append(
                FunctionDocstringData(
                    module_name=get_source_file_name(parsed_element=parsed_function),
                    function_name=get_element_name(parsed_element=parsed_function),
                    missing_sections=missing_sections,
                    arg_missing_type_or_description=args_missing_stuff,
                    extra_args=extra_args,
                    result_missing_type_or_description=result_badly_formatted,
                )
            )

    assert functions_with_issues_in_docstrings == []
