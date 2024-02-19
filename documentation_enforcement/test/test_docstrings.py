from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from re import compile
from textwrap import dedent
from typing import Any, Pattern

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


convention_checker = ConventionChecker()


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


POSSIBLE_ARGUMENTS_SECTIONS = ["Arguments"]
POSSIBLE_RESULTS_SECTIONS = ["Returns", "Yields"]
POSSIBLE_SUB_PACKAGE_SECTIONS = ["SubPackages"]
POSSIBLE_MODULES_SECTIONS = ["Modules"]

LOOSE_REGEX = compile(r"^\s*(\|\s)?([^\s:]+)\s*.*")

ENFORCED_SUB_PACKAGE_REGEX = compile(r"^\s*\|\s([^\s:]+)\s*:\n?\s*(.+)")
ENFORCED_MODULE_REGEX = compile(r"^\s*\|\s([^\s:]+)\s*:\n?\s*(.+)")
ENFORCED_GOOGLE_ARGS_REGEX = compile(r"^\s*(\w+)\s*(\(.*\))\s*:\n?\s*(.+)")
GOOGLE_RESULT_REGEX = compile(r"^\s*((\w+)\s*:\s*(.+)|None)")


def check_all_elements_in_section_context(
    context: SectionContext,
    required_context_elements: list[str],
    enforced_element_regex: Pattern[str],
    element_doc_malformed_in_section: list[str],
    extra_elements_in_section: list[str],
    elements_missing_from_section: list[str],
) -> None:
    element_docs = []
    for line in context.following_lines:
        if not line[:1].isspace():
            element_docs.append(line)
        else:  # pragma: no cover if no multiline
            element_docs[-1] += line
    missing_elements = set(required_context_elements)
    for element_doc in element_docs:
        loose_match = LOOSE_REGEX.match(element_doc)
        if loose_match:  # pragma: no cover if all pass
            element = loose_match.group(2)
            if element in required_context_elements:
                missing_elements.remove(element)
                enforced_match = enforced_element_regex.match(element_doc)
                if not enforced_match:
                    element_doc_malformed_in_section.append(element)
            else:
                extra_elements_in_section.append(element)
    elements_missing_from_section += sorted(list(missing_elements))


def check_for_section_with_elements_in_contexts(
    contexts: dict[str, SectionContext],
    section_group_to_check_for: list[str],
    required_context_elements: list[str],
    enforced_element_regex: Pattern[str],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
    element_doc_malformed_in_section: list[str],
    extra_elements_in_section: list[str],
    elements_missing_from_section: list[str],
) -> None:
    if required_context_elements:
        sections_founds = []
        for section in section_group_to_check_for:
            if section in contexts:  # pragma: no cover branch if section group len==1
                sections_founds.append(section)
        if len(sections_founds) == 0:  # pragma: no cover if all pass
            missing_sections.append("|".join(section_group_to_check_for))
        elif len(sections_founds) == 1:
            check_all_elements_in_section_context(
                context=contexts[sections_founds[0]],
                required_context_elements=required_context_elements,
                enforced_element_regex=enforced_element_regex,
                element_doc_malformed_in_section=element_doc_malformed_in_section,
                extra_elements_in_section=extra_elements_in_section,
                elements_missing_from_section=elements_missing_from_section,
            )
        else:  # pragma: no cover if all pass
            clashing_sections.append(sections_founds)


def check_section_context_has_single_element_with_pattern(
    context: SectionContext,
    enforced_element_regex: Pattern[str],
) -> bool:
    element_docs = []
    for line in context.following_lines:
        if not line[:1].isspace():
            element_docs.append(line)
        else:  # pragma: no cover if no multiline
            element_docs[-1] += line
    if len(element_docs) != 1:  # pragma: no cover if all pass
        return False
    else:
        return bool(enforced_element_regex.match(element_docs[0]))


def check_for_section_with_single_element_in_contexts(
    contexts: dict[str, SectionContext],
    section_group_to_check_for: list[str],
    enforced_element_regex: Pattern[str],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
) -> bool:
    sections_founds = []
    for section in section_group_to_check_for:
        if section in contexts:
            sections_founds.append(section)
    if len(sections_founds) == 0:  # pragma: no cover if all pass
        missing_sections.append("|".join(section_group_to_check_for))
    elif len(sections_founds) == 1:
        return check_section_context_has_single_element_with_pattern(
            context=contexts[sections_founds[0]],
            enforced_element_regex=enforced_element_regex,
        )
    else:  # pragma: no cover if all pass
        clashing_sections.append(sections_founds)
    return False  # pragma: no cover if all pass


def get_package_sub_package_section_info(
    root_of_package_to_test: Path,
    parsed_object: Package,
    possible_sub_packages_sections: list[str],
    contexts: dict[str, SectionContext],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
    element_docs_malformed_in_section: list[str],
    extra_elements_in_section: list[str],
    elements_missing_from_section: list[str],
) -> None:
    current_package_path = root_of_package_to_test.joinpath(parsed_object.name).parent
    required_sub_packages = [
        x.name
        for x in current_package_path.glob("*")
        if x.is_dir() and x.name != "__pycache__"
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        section_group_to_check_for=possible_sub_packages_sections,
        required_context_elements=required_sub_packages,
        enforced_element_regex=ENFORCED_SUB_PACKAGE_REGEX,
        missing_sections=missing_sections,
        clashing_sections=clashing_sections,
        element_doc_malformed_in_section=element_docs_malformed_in_section,
        extra_elements_in_section=extra_elements_in_section,
        elements_missing_from_section=elements_missing_from_section,
    )


def get_package_module_section_info(
    root_of_package_to_test: Path,
    parsed_object: Package,
    possible_sub_packages_sections: list[str],
    contexts: dict[str, SectionContext],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
    element_docs_malformed_in_section: list[str],
    extra_elements_in_section: list[str],
    elements_missing_from_section: list[str],
) -> None:
    current_package_path = root_of_package_to_test.joinpath(parsed_object.name).parent
    required_modules = [
        x.name
        for x in current_package_path.glob("*")
        if x.is_file() and x.name != "__init__.py" and x.name.endswith(".py")
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        section_group_to_check_for=possible_sub_packages_sections,
        required_context_elements=required_modules,
        enforced_element_regex=ENFORCED_MODULE_REGEX,
        missing_sections=missing_sections,
        clashing_sections=clashing_sections,
        element_doc_malformed_in_section=element_docs_malformed_in_section,
        extra_elements_in_section=extra_elements_in_section,
        elements_missing_from_section=elements_missing_from_section,
    )


@dataclass
class PackageDocstringData:
    module_name: str
    missing_sections: list[str]
    clashing_sections: list[str]
    extra_sub_packages: list[str]
    missing_sub_packages: list[str]
    malformed_sub_package_docs: list[str]
    extra_modules: list[str]
    missing_modules: list[str]
    malformed_module_docs: list[str]


def test_all_package_docstrings(package_to_test: Path):
    packages_with_issues_in_docstrings = []
    for parsed_package in get_all_packages_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(
            docstring=parsed_package.docstring,
            sections_to_consider=POSSIBLE_SUB_PACKAGE_SECTIONS
            + POSSIBLE_MODULES_SECTIONS,
        )
        missing_sections = []
        clashing_sections = []
        malformed_sub_package_docs = []
        extra_sub_packages = []
        missing_sub_packages = []
        get_package_sub_package_section_info(
            root_of_package_to_test=package_to_test,
            parsed_object=parsed_package,
            possible_sub_packages_sections=POSSIBLE_SUB_PACKAGE_SECTIONS,
            contexts=contexts,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
            element_docs_malformed_in_section=malformed_sub_package_docs,
            extra_elements_in_section=extra_sub_packages,
            elements_missing_from_section=missing_sub_packages,
        )
        malformed_module_docs = []
        extra_modules = []
        missing_modules = []
        get_package_module_section_info(
            root_of_package_to_test=package_to_test,
            parsed_object=parsed_package,
            possible_sub_packages_sections=POSSIBLE_MODULES_SECTIONS,
            contexts=contexts,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
            element_docs_malformed_in_section=malformed_module_docs,
            extra_elements_in_section=extra_modules,
            elements_missing_from_section=missing_modules,
        )
        if (
            missing_sections
            or clashing_sections
            or malformed_sub_package_docs
            or extra_sub_packages
            or missing_modules
            or malformed_module_docs
            or extra_modules
            or missing_modules
        ):  # pragma: no cover if all pass
            packages_with_issues_in_docstrings.append(
                PackageDocstringData(
                    module_name=get_source_file_name(parsed_element=parsed_package),
                    missing_sections=missing_sections,
                    clashing_sections=clashing_sections,
                    extra_sub_packages=extra_sub_packages,
                    missing_sub_packages=missing_sub_packages,
                    malformed_sub_package_docs=malformed_sub_package_docs,
                    extra_modules=extra_modules,
                    missing_modules=missing_modules,
                    malformed_module_docs=malformed_module_docs,
                )
            )
    assert packages_with_issues_in_docstrings == []


def test_all_module_docstrings(package_to_test: Path):
    for parsed_module in get_all_modules_in(package_to_test=package_to_test):
        assert parsed_module is not None


def test_all_class_docstrings(package_to_test: Path):
    for parsed_class in get_all_classes_in(package_to_test=package_to_test):
        assert parsed_class is not None


def get_function_args_section_info(
    parsed_object: Method | Function,
    possible_arguments_sections: list[str],
    contexts: dict[str, SectionContext],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
    element_docs_malformed_in_section: list[str],
    extra_elements_in_section: list[str],
    elements_missing_from_section: list[str],
) -> None:
    required_arg_docs = [
        x for x in parsed_object.callable_args if x not in ["self", "cls"]
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        section_group_to_check_for=possible_arguments_sections,
        required_context_elements=required_arg_docs,
        enforced_element_regex=ENFORCED_GOOGLE_ARGS_REGEX,
        missing_sections=missing_sections,
        clashing_sections=clashing_sections,
        element_doc_malformed_in_section=element_docs_malformed_in_section,
        extra_elements_in_section=extra_elements_in_section,
        elements_missing_from_section=elements_missing_from_section,
    )


def get_function_results_section_info(
    contexts: dict[str, SectionContext],
    possible_result_sections: list[str],
    missing_sections: list[str],
    clashing_sections: list[list[str]],
) -> bool:
    return check_for_section_with_single_element_in_contexts(
        contexts=contexts,
        section_group_to_check_for=possible_result_sections,
        enforced_element_regex=GOOGLE_RESULT_REGEX,
        missing_sections=missing_sections,
        clashing_sections=clashing_sections,
    )


@dataclass
class FunctionDocstringData:
    module_name: str
    function_name: str
    missing_sections: list[str]
    clashing_sections: list[str]
    missing_args: list[str]
    extra_args: list[str]
    malformed_arg_docs: list[str]
    result_missing_type_or_description: bool


@dataclass
class MethodDocstringData(FunctionDocstringData):
    pass


def test_all_method_docstrings(package_to_test: Path):
    method_with_issues_in_docstrings = []
    for parsed_method in get_all_methods_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(
            docstring=parsed_method.docstring,
            sections_to_consider=POSSIBLE_ARGUMENTS_SECTIONS
            + POSSIBLE_RESULTS_SECTIONS,
        )
        missing_sections = []
        clashing_sections = []
        malformed_arg_docs = []
        extra_args = []
        missing_args = []
        get_function_args_section_info(
            parsed_object=parsed_method,
            possible_arguments_sections=POSSIBLE_ARGUMENTS_SECTIONS,
            contexts=contexts,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
            element_docs_malformed_in_section=malformed_arg_docs,
            extra_elements_in_section=extra_args,
            elements_missing_from_section=missing_args,
        )
        result_badly_formatted = not get_function_results_section_info(
            contexts=contexts,
            possible_result_sections=POSSIBLE_RESULTS_SECTIONS,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
        )
        if (
            missing_sections
            or clashing_sections
            or malformed_arg_docs
            or extra_args
            or missing_args
            or result_badly_formatted
        ):  # pragma: no cover if all pass
            method_with_issues_in_docstrings.append(
                MethodDocstringData(
                    module_name=get_source_file_name(parsed_element=parsed_method),
                    function_name=get_element_name(parsed_element=parsed_method),
                    missing_sections=missing_sections,
                    clashing_sections=clashing_sections,
                    missing_args=missing_args,
                    extra_args=extra_args,
                    malformed_arg_docs=malformed_arg_docs,
                    result_missing_type_or_description=result_badly_formatted,
                )
            )

    assert method_with_issues_in_docstrings == []


def test_all_function_docstrings(package_to_test: Path):
    functions_with_issues_in_docstrings = []
    for parsed_function in get_all_functions_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(
            docstring=parsed_function.docstring,
            sections_to_consider=POSSIBLE_ARGUMENTS_SECTIONS
            + POSSIBLE_RESULTS_SECTIONS,
        )
        missing_sections = []
        clashing_sections = []
        malformed_arg_docs = []
        extra_args = []
        missing_args = []
        get_function_args_section_info(
            parsed_object=parsed_function,
            possible_arguments_sections=POSSIBLE_ARGUMENTS_SECTIONS,
            contexts=contexts,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
            element_docs_malformed_in_section=malformed_arg_docs,
            extra_elements_in_section=extra_args,
            elements_missing_from_section=missing_args,
        )
        result_badly_formatted = not get_function_results_section_info(
            contexts=contexts,
            possible_result_sections=POSSIBLE_RESULTS_SECTIONS,
            missing_sections=missing_sections,
            clashing_sections=clashing_sections,
        )
        if (
            missing_sections
            or clashing_sections
            or malformed_arg_docs
            or extra_args
            or result_badly_formatted
        ):  # pragma: no cover if all pass
            functions_with_issues_in_docstrings.append(
                FunctionDocstringData(
                    module_name=get_source_file_name(parsed_element=parsed_function),
                    function_name=get_element_name(parsed_element=parsed_function),
                    missing_sections=missing_sections,
                    clashing_sections=clashing_sections,
                    missing_args=missing_args,
                    extra_args=extra_args,
                    malformed_arg_docs=malformed_arg_docs,
                    result_missing_type_or_description=result_badly_formatted,
                )
            )

    assert functions_with_issues_in_docstrings == []
