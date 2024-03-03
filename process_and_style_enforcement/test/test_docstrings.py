import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from re import compile
from textwrap import dedent
from typing import NamedTuple, Pattern, TypeAlias

import pytest
from _pytest.fixtures import SubRequest
from pydocstyle import ConventionChecker
from pydocstyle.parser import Class, Function, Method, Module, Package, Parser

DocumentationElement: TypeAlias = Class | Function | Method | Module | Package

sub_projects_to_enforce_docstrings = ["pypi_package", "build_support"]


@pytest.fixture(params=sub_projects_to_enforce_docstrings)
def package_to_test(real_project_root_dir: Path, request: SubRequest) -> Path:
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


def get_flattened_public_children(
    element_to_flatten: DocumentationElement,
) -> list[DocumentationElement]:
    flattened_list = [element_to_flatten]
    for child in element_to_flatten.children:
        if child.is_public:  # pragma: no cover - branching, all could be public
            flattened_list += get_flattened_public_children(element_to_flatten=child)
    return flattened_list


def parse_all_objects(package_to_test: Path) -> list[DocumentationElement]:
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
    return get_source_file_name(parsed_element=parsed_element.parent)


def get_element_name(
    parsed_element: Package | Module | Class | Function | Method,
    suffix_to_add: str | None = None,
) -> str:  # pragma: no cover if all pass
    if not suffix_to_add:
        suffix_to_add = ""
    if isinstance(parsed_element, (Package, Module)):
        return suffix_to_add
    if suffix_to_add:
        suffix_to_add = parsed_element.name + "." + suffix_to_add
    else:
        suffix_to_add = parsed_element.name
    return get_element_name(
        parsed_element=parsed_element.parent, suffix_to_add=suffix_to_add
    )


convention_checker = ConventionChecker()


class SectionContext(NamedTuple):
    section_name: str
    previous_line: str
    line: int
    following_lines: list[str]
    original_index: int
    is_last_section: bool


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


def get_docstring_contexts(docstring: str) -> dict[str, SectionContext]:
    lines = docstring.split("\n")
    return {
        context.section_name: normalize_context(context=context)
        for context in convention_checker._get_section_contexts(  # noqa: SLF001
            lines,
            sorted(
                set(
                    list(convention_checker.GOOGLE_SECTION_NAMES)
                    + PROJECT_SPECIFIC_SECTIONS
                )
            ),
        )
    }


POSSIBLE_ATTRIBUTES_SECTIONS = ["Attributes"]
POSSIBLE_ARGUMENTS_SECTIONS = ["Args"]
POSSIBLE_RESULTS_SECTIONS = ["Returns", "Yields"]
POSSIBLE_SUB_PACKAGE_SECTIONS = ["SubPackages"]
POSSIBLE_MODULES_SECTIONS = ["Modules"]

PROJECT_SPECIFIC_SECTIONS = sorted(
    {
        section_name
        for list_of_sections in (
            POSSIBLE_ATTRIBUTES_SECTIONS,
            POSSIBLE_ARGUMENTS_SECTIONS,
            POSSIBLE_RESULTS_SECTIONS,
            POSSIBLE_SUB_PACKAGE_SECTIONS,
            POSSIBLE_MODULES_SECTIONS,
        )
        for section_name in list_of_sections
    }
)

LOOSE_REGEX = compile(r"^\s*(\|\s)?([^\s:]+)\s*.*")

ENFORCED_SUB_PACKAGE_REGEX = compile(r"^\s*\|\s([^\s:]+)\s*:\n?\s*(.+)")
ENFORCED_MODULE_REGEX = compile(r"^\s*\|\s([^\s:]+)\s*:\n?\s*(.+)")
ENFORCED_ATTRIBUTE_REGEX = compile(r"^\s*\|\s([^\s:]+)\s*:\n?\s*(.+)")
ENFORCED_GOOGLE_ARGS_REGEX = compile(r"^\s*(\w+)\s*(\(.*\))\s*:\n?\s*(.+)")
GOOGLE_RESULT_REGEX = compile(r"^\s*(([\w\[\],\s]+)\s*:\s*(.+)|None)")


@dataclass
class SectionElementData:
    possible_section_names: list[str]
    required_context_elements: list[str]
    enforced_element_regex: Pattern[str] | None

    extra_elements: list[str]
    missing_elements: list[str]
    malformed_element_docs: list[str]

    def has_issues(self) -> bool:
        if (
            self.extra_elements or self.missing_elements or self.malformed_element_docs
        ):  # pragma: no cover if all tests pass
            return True
        return False


@dataclass
class GenericDocstringData:
    module_name: str
    missing_sections: list[str]
    clashing_sections: list[str]
    sections: dict[str, SectionElementData]

    def has_issues(self) -> bool:
        if (
            self.missing_sections
            or self.clashing_sections
            or any(section.has_issues() for section in self.sections.values())
        ):  # pragma: no cover if all tests pass
            return True
        return False


@dataclass
class ElementDocstringData(GenericDocstringData):
    name: str


def check_all_elements_in_section_context(
    context: SectionContext,
    required_context_elements: list[str],
    enforced_element_regex: Pattern[str],
    section_element_data: SectionElementData,
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
                    section_element_data.malformed_element_docs.append(element)
            else:
                section_element_data.extra_elements.append(element)
    section_element_data.missing_elements += sorted(missing_elements)


def check_for_section_with_elements_in_contexts(
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    if section_element_data.required_context_elements:
        sections_founds = [
            section
            for section in section_element_data.possible_section_names
            if section in contexts
        ]
        if len(sections_founds) == 0:  # pragma: no cover if all pass
            docstring_data.missing_sections.append(
                "|".join(section_element_data.possible_section_names)
            )
        elif len(sections_founds) == 1:
            check_all_elements_in_section_context(
                context=contexts[sections_founds[0]],
                required_context_elements=section_element_data.required_context_elements,
                enforced_element_regex=section_element_data.enforced_element_regex,
                section_element_data=section_element_data,
            )
        else:  # pragma: no cover if all pass
            docstring_data.clashing_sections.append("|".join(sections_founds))


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
    return bool(enforced_element_regex.match(element_docs[0]))


def check_for_section_with_single_element_in_contexts(
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> bool:
    section_element_data = docstring_data.sections[section_name]
    section_group_to_check_for = section_element_data.possible_section_names
    sections_founds = [
        section for section in section_group_to_check_for if section in contexts
    ]
    if len(sections_founds) == 0:  # pragma: no cover if all pass
        docstring_data.missing_sections.append("|".join(section_group_to_check_for))
    elif len(sections_founds) == 1:
        return check_section_context_has_single_element_with_pattern(
            context=contexts[sections_founds[0]],
            enforced_element_regex=section_element_data.enforced_element_regex,
        )
    else:  # pragma: no cover if all pass
        docstring_data.clashing_sections.append("|".join(sections_founds))
    return False  # pragma: no cover if all pass


def get_package_sub_package_section_info(
    root_of_package_to_test: Path,
    parsed_object: Package,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    current_package_path = root_of_package_to_test.joinpath(parsed_object.name).parent
    section_element_data.required_context_elements = [
        x.name
        for x in current_package_path.glob("*")
        if x.is_dir() and x.name != "__pycache__"
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


def get_package_module_section_info(
    root_of_package_to_test: Path,
    parsed_object: Package,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    current_package_path = root_of_package_to_test.joinpath(parsed_object.name).parent
    section_element_data.required_context_elements = [
        x.name
        for x in current_package_path.glob("*")
        if x.is_file() and x.name != "__init__.py" and x.name.endswith(".py")
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


@dataclass
class PackageDocstringData(GenericDocstringData):
    pass


def test_all_package_docstrings(package_to_test: Path) -> None:
    packages_with_issues_in_docstrings = []
    for parsed_package in get_all_packages_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(docstring=parsed_package.docstring)
        package_docstring_data = PackageDocstringData(
            module_name=get_source_file_name(parsed_element=parsed_package),
            missing_sections=[],
            clashing_sections=[],
            sections={
                "sub_packages": SectionElementData(
                    possible_section_names=POSSIBLE_SUB_PACKAGE_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=ENFORCED_SUB_PACKAGE_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
                "modules": SectionElementData(
                    possible_section_names=POSSIBLE_MODULES_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=ENFORCED_MODULE_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
            },
        )
        get_package_sub_package_section_info(
            root_of_package_to_test=package_to_test,
            parsed_object=parsed_package,
            contexts=contexts,
            docstring_data=package_docstring_data,
            section_name="sub_packages",
        )
        get_package_module_section_info(
            root_of_package_to_test=package_to_test,
            parsed_object=parsed_package,
            contexts=contexts,
            docstring_data=package_docstring_data,
            section_name="modules",
        )
        if package_docstring_data.has_issues():  # pragma: no cover if all pass
            packages_with_issues_in_docstrings.append(package_docstring_data)
    assert packages_with_issues_in_docstrings == []


def import_element(
    full_module_path: str, full_element_path: str | None = None
) -> DocumentationElement:
    imported_element = __import__(full_module_path)
    for path_element in full_module_path.split(".")[1:]:
        imported_element = getattr(imported_element, path_element)
    if full_element_path is not None:  # pragma: no cover - might not have element path
        for path_element in full_element_path.split("."):
            imported_element = getattr(imported_element, path_element)
    return imported_element


def get_list_of_imported_names(module_source_text: str) -> set[str]:
    names_imported = set()
    parsed_module = ast.parse(module_source_text)
    for node in ast.iter_child_nodes(parsed_module):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:
                names_imported.add(name.asname if name.asname else name.name)
    return names_imported


def get_module_attributes_section_info(
    parsed_object: Module,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    # remove ".py"
    module_path = get_source_file_name(parsed_element=parsed_object)[:-3].replace(
        "/", "."
    )
    imported_module = import_element(full_module_path=module_path)
    names_imported_by_module = get_list_of_imported_names(
        module_source_text=parsed_object.source
    )
    module_child_names = {child.name for child in parsed_object.children}
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = [
        name
        for name in dir(imported_module)
        if not (
            name.startswith(("_", "@"))
            or name in names_imported_by_module
            or name in module_child_names
        )
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


@dataclass
class ModuleDocstringData(GenericDocstringData):
    pass


def test_all_module_docstrings(package_to_test: Path) -> None:
    modules_with_issues_in_docstrings = []
    for parsed_module in get_all_modules_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(docstring=parsed_module.docstring)
        module_docstring_data = ModuleDocstringData(
            module_name=get_source_file_name(parsed_element=parsed_module),
            missing_sections=[],
            clashing_sections=[],
            sections={
                "attributes": SectionElementData(
                    possible_section_names=POSSIBLE_ATTRIBUTES_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=ENFORCED_ATTRIBUTE_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
            },
        )
        get_module_attributes_section_info(
            parsed_object=parsed_module,
            contexts=contexts,
            docstring_data=module_docstring_data,
            section_name="attributes",
        )
        if module_docstring_data.has_issues():  # pragma: no cover if all pass
            modules_with_issues_in_docstrings.append(module_docstring_data)
    assert modules_with_issues_in_docstrings == []


def test_all_class_docstrings(package_to_test: Path) -> None:
    for parsed_class in get_all_classes_in(package_to_test=package_to_test):
        assert parsed_class is not None


def get_function_args_section_info(
    parsed_object: Method | Function,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    # remove ".py"
    module_path = get_source_file_name(parsed_element=parsed_object)[:-3].replace(
        "/", "."
    )
    imported_function = import_element(
        full_module_path=module_path,
        full_element_path=get_element_name(parsed_element=parsed_object),
    )
    parameters = list(inspect.signature(imported_function).parameters)
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = [
        x
        for x in parsed_object.callable_args
        # We have to check against real parameters because sometimes
        # the parsed object lists complex type hints as callable args
        if x not in ["self", "cls"] and x in parameters
    ]
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


def get_error_in_function_results_section_info(
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> bool:
    return not check_for_section_with_single_element_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


@dataclass
class FunctionDocstringData(ElementDocstringData):
    result_missing_type_or_description: bool | None

    def has_issues(self) -> bool:
        if (
            super().has_issues() or self.result_missing_type_or_description
        ):  # pragma: no cover if all tests pass
            return True
        return False


@dataclass
class MethodDocstringData(FunctionDocstringData):
    """Different name for convenience."""


def test_all_method_docstrings(package_to_test: Path) -> None:
    method_with_issues_in_docstrings = []
    for parsed_method in get_all_methods_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(docstring=parsed_method.docstring)
        method_docstring_data = MethodDocstringData(
            module_name=get_source_file_name(parsed_element=parsed_method),
            name=get_element_name(parsed_element=parsed_method),
            missing_sections=[],
            clashing_sections=[],
            sections={
                "args": SectionElementData(
                    possible_section_names=POSSIBLE_ARGUMENTS_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=ENFORCED_GOOGLE_ARGS_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
                "results": SectionElementData(
                    possible_section_names=POSSIBLE_RESULTS_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=GOOGLE_RESULT_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
            },
            result_missing_type_or_description=None,
        )
        get_function_args_section_info(
            parsed_object=parsed_method,
            contexts=contexts,
            docstring_data=method_docstring_data,
            section_name="args",
        )
        method_docstring_data.result_missing_type_or_description = (
            get_error_in_function_results_section_info(
                contexts=contexts,
                docstring_data=method_docstring_data,
                section_name="results",
            )
        )
        if method_docstring_data.has_issues():  # pragma: no cover if all pass
            method_with_issues_in_docstrings.append(method_docstring_data)
    assert method_with_issues_in_docstrings == []


def test_all_function_docstrings(package_to_test: Path) -> None:
    functions_with_issues_in_docstrings = []
    for parsed_function in get_all_functions_in(package_to_test=package_to_test):
        contexts = get_docstring_contexts(docstring=parsed_function.docstring)
        function_docstring_data = FunctionDocstringData(
            module_name=get_source_file_name(parsed_element=parsed_function),
            name=get_element_name(parsed_element=parsed_function),
            missing_sections=[],
            clashing_sections=[],
            sections={
                "args": SectionElementData(
                    possible_section_names=POSSIBLE_ARGUMENTS_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=ENFORCED_GOOGLE_ARGS_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
                "results": SectionElementData(
                    possible_section_names=POSSIBLE_RESULTS_SECTIONS,
                    required_context_elements=[],
                    enforced_element_regex=GOOGLE_RESULT_REGEX,
                    extra_elements=[],
                    missing_elements=[],
                    malformed_element_docs=[],
                ),
            },
            result_missing_type_or_description=None,
        )
        get_function_args_section_info(
            parsed_object=parsed_function,
            contexts=contexts,
            docstring_data=function_docstring_data,
            section_name="args",
        )
        function_docstring_data.result_missing_type_or_description = (
            get_error_in_function_results_section_info(
                contexts=contexts,
                docstring_data=function_docstring_data,
                section_name="results",
            )
        )
        if function_docstring_data.has_issues():  # pragma: no cover if all pass
            functions_with_issues_in_docstrings.append(function_docstring_data)
    assert functions_with_issues_in_docstrings == []
