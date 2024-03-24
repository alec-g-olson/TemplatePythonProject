import ast
import re
from dataclasses import dataclass
from inspect import getmembers, isclass, isfunction, ismodule, signature, unwrap
from pathlib import Path
from re import compile
from textwrap import dedent
from types import FunctionType, ModuleType
from typing import Any, Iterable, Pattern, Type, TypeAlias

import pytest
from _pytest.fixtures import SubRequest

from build_support.ci_cd_vars.project_setting_vars import get_project_name
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_all_python_subprojects_with_src,
)

ImportedElement: TypeAlias = (
    ModuleType | FunctionType | classmethod | staticmethod | Type
)


@dataclass(frozen=True)
class PackageInfo:
    module_path: str
    docstring: str
    sub_packages: list[str]
    modules: dict[str, ModuleType]


@dataclass(frozen=True)
class ModuleInfo:
    module_path: str
    docstring: str
    attributes: dict[str, Any]
    classes: dict[str, Type]
    functions: dict[str, FunctionType]


@dataclass(frozen=True)
class ClassInfo:
    module_path: str
    docstring: str
    element_path: str
    methods: dict[str, FunctionType | classmethod | staticmethod]


@dataclass(frozen=True)
class FunctionInfo:
    module_path: str
    docstring: str
    element_path: str
    args: list[str]


DocumentationElement: TypeAlias = PackageInfo | ModuleInfo | ClassInfo | FunctionInfo

PROJECT_ROOT = Path(__file__).parent.parent.parent

subprojects_with_src = get_all_python_subprojects_with_src(project_root=PROJECT_ROOT)


@pytest.fixture(params=subprojects_with_src, scope="module")
def package_to_test(request: SubRequest) -> str:
    context_with_src = request.param.subproject_context
    if context_with_src == SubprojectContext.PYPI:
        return get_project_name(project_root=PROJECT_ROOT)
    return context_with_src.value


def import_element(
    full_module_path: str, full_element_path: str | None = None
) -> ImportedElement:
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


def parse_package_info(imported_package: ModuleType) -> PackageInfo:
    sub_packages = []
    modules = {}
    if imported_package.__file__ is None:  # pragma: no cover not hit if pass
        msg = f"{imported_package.__name__} is does not have a file path."
        raise ValueError(msg)
    package_path = Path(imported_package.__file__)
    for package_file_or_folder in package_path.parent.glob("*"):
        file_or_folder_name = package_file_or_folder.name
        if file_or_folder_name.startswith("_"):
            continue
        if package_file_or_folder.is_file() and file_or_folder_name[-3:] == ".py":
            module_name = file_or_folder_name[:-3]
            module_path = f"{imported_package.__package__}.{module_name}"
            imported_module = import_element(full_module_path=module_path)
            if not isinstance(imported_module, ModuleType):  # pragma: no cover
                msg = f"{imported_module.__name__} is not a module."
                raise ValueError(msg)
            modules[module_name] = imported_module
        if package_file_or_folder.is_dir():
            sub_packages.append(file_or_folder_name)
    if imported_package.__doc__ is None:  # pragma: no cover
        imported_package.__doc__ = ""
    return PackageInfo(
        module_path=imported_package.__name__,
        docstring=imported_package.__doc__,
        sub_packages=sub_packages,
        modules=modules,
    )


def parse_module_info(imported_module: ModuleType) -> ModuleInfo:
    if imported_module.__file__ is None:  # pragma: no cover not hit if pass
        msg = f"{imported_module.__name__} is does not have a file path."
        raise ValueError(msg)
    module_path = Path(imported_module.__file__)
    module_text = module_path.read_text()
    names_imported_by_module = get_list_of_imported_names(
        module_source_text=module_text
    )
    attributes = {}
    classes = {}
    functions = {}
    for name, member in getmembers(imported_module):
        unwrapped_member = unwrap(member)
        if not (name.startswith(("_", "@")) or name in names_imported_by_module):
            if isfunction(unwrapped_member):
                functions[name] = unwrapped_member
            elif isclass(unwrapped_member):
                classes[name] = unwrapped_member
            else:
                attributes[name] = unwrapped_member
    if imported_module.__doc__ is None:  # pragma: no cover
        imported_module.__doc__ = ""
    return ModuleInfo(
        module_path=imported_module.__name__,
        docstring=imported_module.__doc__,
        attributes=attributes,
        classes=classes,
        functions=functions,
    )


def parse_class_info(imported_class: Type, element_prefix: str) -> ClassInfo:
    methods = {}
    class_elements = dict(vars(imported_class))
    dataclass_params = class_elements.get("__dataclass_params__")
    methods_to_ignore = ["__new__"]
    if dataclass_params:  # pragma: no cover - might not have dataclasses in src
        if dataclass_params.eq:
            methods_to_ignore.extend(["__eq__", "__hash__"])
        if dataclass_params.init:
            methods_to_ignore.append("__init__")
        if dataclass_params.repr:
            methods_to_ignore.append("__repr__")
        if dataclass_params.frozen:
            methods_to_ignore.extend(["__setattr__", "__delattr__"])
    for name, member in vars(imported_class).items():
        if (
            (isfunction(member) or isinstance(member, (staticmethod, classmethod)))
            and (
                not name.startswith("_")
                or (name.startswith("__") and name.endswith("__"))
            )
            and name not in methods_to_ignore
        ):
            methods[name] = member
    if imported_class.__doc__ is None:  # pragma: no cover
        imported_class.__doc__ = ""
    return ClassInfo(
        module_path=imported_class.__module__,
        element_path=f"{element_prefix}.{imported_class.__name__}"
        if element_prefix
        else imported_class.__name__,
        docstring=imported_class.__doc__,
        methods=methods,
    )


def parse_function_info(
    imported_function: FunctionType | classmethod | staticmethod, element_prefix: str
) -> FunctionInfo:
    if isinstance(imported_function, (classmethod, staticmethod)):
        params = signature(imported_function.__func__).parameters
    else:
        params = signature(imported_function).parameters
    args = [param for param in params if param not in {"self", "cls"}]
    if imported_function.__doc__ is None:  # pragma: no cover
        imported_function.__doc__ = ""
    return FunctionInfo(
        module_path=imported_function.__module__,
        element_path=f"{element_prefix}.{imported_function.__name__}"
        if element_prefix
        else imported_function.__name__,
        docstring=imported_function.__doc__,
        args=args,
    )


def parse_sub_elements(
    imported_element: ImportedElement,
    all_element_info: list[DocumentationElement],
    element_prefix: str = "",
) -> None:
    if ismodule(imported_element):
        if imported_element.__file__ is None:  # pragma: no cover not hit if pass
            msg = f"{imported_element.__name__} is does not have a file path."
            raise ValueError(msg)
        if imported_element.__file__.endswith("__init__.py"):
            parsed_package = parse_package_info(imported_package=imported_element)
            all_element_info.append(parsed_package)
            for sub_package in parsed_package.sub_packages:
                sub_package_path = f"{imported_element.__package__}.{sub_package}"
                parse_sub_elements(
                    imported_element=import_element(full_module_path=sub_package_path),
                    all_element_info=all_element_info,
                )
            for imported_module in parsed_package.modules.values():
                parse_sub_elements(
                    imported_element=imported_module,
                    all_element_info=all_element_info,
                )
        else:
            parsed_module = parse_module_info(imported_module=imported_element)
            all_element_info.append(parsed_module)
            for imported_class in parsed_module.classes.values():
                parse_sub_elements(
                    imported_element=imported_class,
                    all_element_info=all_element_info,
                )
            for imported_function in parsed_module.functions.values():
                parse_sub_elements(
                    imported_element=imported_function,
                    all_element_info=all_element_info,
                )
    elif isfunction(imported_element) or isinstance(
        imported_element, (staticmethod, classmethod)
    ):
        parsed_function = parse_function_info(
            imported_function=imported_element, element_prefix=element_prefix
        )
        all_element_info.append(parsed_function)
    elif isinstance(imported_element, type):
        parsed_class = parse_class_info(
            imported_class=imported_element, element_prefix=element_prefix
        )
        all_element_info.append(parsed_class)
        for imported_method in parsed_class.methods.values():
            parse_sub_elements(
                imported_element=imported_method,
                all_element_info=all_element_info,
                element_prefix=element_prefix + imported_method.__name__,
            )
    else:  # pragma: no cover not hit if everything is working
        msg = f"{imported_element.__name__} is not a supported type."
        raise ValueError(msg)


@pytest.fixture(scope="module")
def parse_all_elements(package_to_test: str) -> list[DocumentationElement]:
    top_level_package = import_element(full_module_path=package_to_test)
    all_elements: list[DocumentationElement] = []
    parse_sub_elements(
        imported_element=top_level_package, all_element_info=all_elements
    )
    return all_elements


@pytest.fixture(scope="module")
def all_packages_info(
    parse_all_elements: list[DocumentationElement],
) -> list[PackageInfo]:
    return [obj for obj in parse_all_elements if isinstance(obj, PackageInfo)]


@pytest.fixture(scope="module")
def all_modules_info(
    parse_all_elements: list[DocumentationElement],
) -> list[ModuleInfo]:
    return [obj for obj in parse_all_elements if isinstance(obj, ModuleInfo)]


@pytest.fixture(scope="module")
def all_class_info(parse_all_elements: list[DocumentationElement]) -> list[ClassInfo]:
    return [obj for obj in parse_all_elements if isinstance(obj, ClassInfo)]


@pytest.fixture(scope="module")
def all_function_info(
    parse_all_elements: list[DocumentationElement],
) -> list[FunctionInfo]:
    return [obj for obj in parse_all_elements if isinstance(obj, FunctionInfo)]


@dataclass(frozen=True)
class SectionContext:
    section_name: str
    previous_line: str
    line: str
    following_lines: list[str]
    original_index: int
    is_last_section: bool


def get_leading_words(line: str) -> str:
    """Return any leading set of words from `line`.

    For example, if `line` is "  Hello world!!!", returns "Hello world".
    """
    result = re.compile(r"[\w ]+").match(line.strip())
    if result is not None:
        return result.group()
    return ""


def is_docstring_section(context: SectionContext) -> bool:
    section_name_suffix = (
        context.line.strip().lstrip(context.section_name.strip()).strip()
    )

    section_suffix_is_only_colon = section_name_suffix == ":"

    punctuation = [",", ";", ".", "-", "\\", "/", "]", "}", ")"]
    prev_line_ends_with_punctuation = any(
        context.previous_line.strip().endswith(x) for x in punctuation
    )

    this_line_looks_like_a_section_name = (
        len(section_name_suffix.strip()) == 0 or section_suffix_is_only_colon
    )

    prev_line_looks_like_end_of_paragraph = (
        prev_line_ends_with_punctuation or len(context.previous_line.strip()) == 0
    )

    return this_line_looks_like_a_section_name and prev_line_looks_like_end_of_paragraph


def get_section_context(
    lines: list[str], valid_section_names: Iterable[str]
) -> Iterable[SectionContext]:
    lower_section_names = [s.lower() for s in valid_section_names]

    def _suspected_as_section(_line: str) -> bool:
        result = get_leading_words(_line.lower())
        return result in lower_section_names

    # Finding our suspects.
    suspected_section_indices = [
        i for i, line in enumerate(lines) if _suspected_as_section(line)
    ]

    # First - create a list of possible contexts. Note that the
    # `following_lines` member is until the end of the docstring.
    contexts = []
    for i in suspected_section_indices:
        last_index = i - 1
        next_index = i + 1
        contexts.append(
            SectionContext(
                get_leading_words(lines[i].strip()),
                lines[last_index],
                lines[i],
                lines[next_index:],
                i,
                False,
            )
        )

    # Now that we have manageable objects - rule out false positives.
    contexts = [c for c in contexts if is_docstring_section(c)]

    # Now we shall trim the `following lines` field to only reach the
    # next section name.
    for i in range(len(contexts)):
        current_context = contexts[i]
        next_context = None if i == len(contexts) - 1 else contexts[i + 1]
        end = -1 if next_context is None else next_context.original_index
        next_index = current_context.original_index + 1
        yield SectionContext(
            current_context.section_name,
            current_context.previous_line,
            current_context.line,
            lines[next_index:end],
            current_context.original_index,
            next_context is None,
        )


def normalize_context(context: SectionContext) -> SectionContext:
    lines = context.following_lines
    if context.following_lines:  # pragma: no cover - all context might have lines
        first_line = context.following_lines[0]
        leading_whitespaces = first_line[: -len(first_line.lstrip())]
        lines = [
            line
            for line in context.following_lines
            if line.startswith(leading_whitespaces) or line == ""
        ]

    args_content = dedent("\n".join(lines)).strip()
    return SectionContext(
        section_name=context.section_name,
        previous_line=context.previous_line,
        line=context.line,
        following_lines=args_content.splitlines(keepends=True),
        original_index=context.original_index,
        is_last_section=context.is_last_section,
    )


def get_docstring_contexts(docstring: str) -> dict[str, SectionContext]:
    lines = docstring.split("\n") if docstring else []
    return {
        context.section_name: normalize_context(context=context)
        for context in get_section_context(
            lines,
            sorted(set(GOOGLE_SECTION_NAMES + PROJECT_SPECIFIC_SECTIONS)),
        )
    }


GOOGLE_SECTION_NAMES = [
    "Args",
    "Arguments",
    "Attention",
    "Attributes",
    "Caution",
    "Danger",
    "Error",
    "Example",
    "Examples",
    "Hint",
    "Important",
    "Keyword Args",
    "Keyword Arguments",
    "Methods",
    "Note",
    "Notes",
    "Return",
    "Returns",
    "Raises",
    "References",
    "See Also",
    "Tip",
    "Todo",
    "Warning",
    "Warnings",
    "Warns",
    "Yield",
    "Yields",
]


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
    enforced_element_regex: Pattern[str]

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
    module: str
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
    section_element = docstring_data.sections[section_name]
    if section_element.required_context_elements:
        sections_founds = [
            section
            for section in section_element.possible_section_names
            if section in contexts
        ]
        if len(sections_founds) == 0:  # pragma: no cover if all pass
            docstring_data.missing_sections.append(
                "|".join(section_element.possible_section_names)
            )
        elif len(sections_founds) == 1:
            check_all_elements_in_section_context(
                context=contexts[sections_founds[0]],
                required_context_elements=section_element.required_context_elements,
                enforced_element_regex=section_element.enforced_element_regex,
                section_element_data=section_element,
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
    parsed_package: PackageInfo,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = parsed_package.sub_packages
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


def get_package_module_section_info(
    parsed_package: PackageInfo,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = list(parsed_package.modules.keys())
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


def test_all_package_docstrings(all_packages_info: list[PackageInfo]) -> None:
    assert len(all_packages_info) != 0
    packages_with_issues_in_docstrings = []
    for package_info in all_packages_info:
        contexts = get_docstring_contexts(docstring=package_info.docstring)
        package_docstring_data = GenericDocstringData(
            module=package_info.module_path,
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
            parsed_package=package_info,
            contexts=contexts,
            docstring_data=package_docstring_data,
            section_name="sub_packages",
        )
        get_package_module_section_info(
            parsed_package=package_info,
            contexts=contexts,
            docstring_data=package_docstring_data,
            section_name="modules",
        )
        if package_docstring_data.has_issues():  # pragma: no cover if all pass
            packages_with_issues_in_docstrings.append(package_docstring_data)
    assert packages_with_issues_in_docstrings == []


def get_module_attributes_section_info(
    parsed_module: ModuleInfo,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = list(
        parsed_module.attributes.keys()
    )
    check_for_section_with_elements_in_contexts(
        contexts=contexts,
        docstring_data=docstring_data,
        section_name=section_name,
    )


def test_all_module_docstrings(
    all_modules_info: list[ModuleInfo], package_to_test: str
) -> None:
    assert len(all_modules_info) != 0 or package_to_test == "pulumi"
    modules_with_issues_in_docstrings = []
    for module_info in all_modules_info:
        contexts = get_docstring_contexts(docstring=module_info.docstring)
        module_docstring_data = GenericDocstringData(
            module=module_info.module_path,
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
            parsed_module=module_info,
            contexts=contexts,
            docstring_data=module_docstring_data,
            section_name="attributes",
        )
        if module_docstring_data.has_issues():  # pragma: no cover if all pass
            modules_with_issues_in_docstrings.append(module_docstring_data)
    assert modules_with_issues_in_docstrings == []


def test_all_class_docstrings(
    all_class_info: list[ClassInfo], package_to_test: str
) -> None:
    assert len(all_class_info) != 0 or package_to_test == "pulumi"
    for class_info in all_class_info:
        assert class_info is not None


def get_function_args_section_info(
    parsed_function: FunctionInfo,
    contexts: dict[str, SectionContext],
    docstring_data: GenericDocstringData,
    section_name: str,
) -> None:
    section_element_data = docstring_data.sections[section_name]
    section_element_data.required_context_elements = parsed_function.args
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


def test_all_function_docstrings(
    all_function_info: list[FunctionInfo], package_to_test: str
) -> None:
    assert len(all_function_info) != 0 or package_to_test == "pulumi"
    functions_with_issues_in_docstrings = []
    for function_info in all_function_info:
        contexts = get_docstring_contexts(docstring=function_info.docstring)
        function_docstring_data = FunctionDocstringData(
            module=function_info.module_path,
            name=function_info.element_path,
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
            parsed_function=function_info,
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
