"""Feature tests for ticket 98: switch static typing from mypy to ty.

Verifies that type checking uses ty, succeeds on the repository, and that
pyproject.toml is configured for ty with no mypy configuration. One test
writes a file per ty rule (each file violates that rule), runs the type
checker once, and parses the output to ensure every rule is flagged.
"""

import re
from pathlib import Path
from subprocess import run
from typing import Any, cast

import pytest
from build_support.ci_cd_vars.docker_vars import DockerTarget, get_docker_image_name
from build_support.ci_cd_vars.project_setting_vars import get_pyproject_toml_data
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)
from test_utils.command_runner import (
    FeatureTestCommandContext,
    run_command_and_save_logs,
)


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_type_checks_use_ty_and_succeed(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """Running make type_checks uses ty and succeeds on the repository."""
    return_code, _, _ = run_command_and_save_logs(
        context=default_command_context, command_args=["type_checks"]
    )
    assert return_code == 0


def test_pyproject_has_ty_config_and_no_mypy(real_project_root_dir: Path) -> None:
    """pyproject.toml contains ty configuration with all checks at error and no mypy."""
    pyproject_data = get_pyproject_toml_data(project_root=real_project_root_dir)
    tool = cast(dict[str, Any], pyproject_data).get("tool")
    assert tool is not None
    assert "ty" in tool
    ty_config = tool["ty"]
    assert "rules" in ty_config
    assert ty_config["rules"].get("all") == "error"
    assert "mypy" not in tool


@pytest.mark.usefixtures("mock_lightweight_project_with_unit_tests_and_feature_tests")
def test_dev_container_has_ty_not_mypy(
    mock_project_root: Path, make_command_prefix: list[str], real_project_root_dir: Path
) -> None:
    """Verify mypy is not available and ty is available in the dev container.

    Runs ``mypy --version`` and ``ty version`` in the development container.
    Mypy must fail with a command-not-found style error; ty must succeed.

    Args:
        mock_project_root (Path): Root of the mock project (dev image context).
        make_command_prefix (list[str]): Make command prefix for running setup_dev_env.
        real_project_root_dir (Path): Root of the real project for image name lookup.
    """
    run(
        [*make_command_prefix, "setup_dev_env"],
        cwd=mock_project_root,
        check=True,
        capture_output=True,
    )
    image = get_docker_image_name(
        project_root=real_project_root_dir, target_image=DockerTarget.DEV
    )
    mount = f"{mock_project_root.resolve()}:/usr/dev"
    docker_run = ["docker", "run", "--rm", "-v", mount, "-w", "/usr/dev", image]

    mypy_result = run(
        [*docker_run, "mypy", "--version"],
        check=False,
        capture_output=True,
        text=True,
        cwd=mock_project_root,
    )
    assert mypy_result.returncode != 0, (
        "mypy should not be available in the dev container; "
        f"stderr: {mypy_result.stderr!r}"
    )
    assert (
        "not found" in mypy_result.stderr.lower()
        or "no such file" in mypy_result.stderr.lower()
    ), (
        "Expected command-not-found style error from mypy; "
        f"stderr: {mypy_result.stderr!r}"
    )

    ty_result = run(
        [*docker_run, "ty", "version"],
        check=False,
        capture_output=True,
        text=True,
        cwd=mock_project_root,
    )
    assert ty_result.returncode == 0, (
        f"ty must be available in the dev container; stderr: {ty_result.stderr!r}"
    )


def _write_pypi_test_file(
    mock_project_root: Path, file_name: str, file_contents: str
) -> None:
    get_python_subproject(
        project_root=mock_project_root, subproject_context=SubprojectContext.PYPI
    ).get_test_dir().joinpath(file_name).write_text(file_contents)


TY_RULES: list[tuple[str, str, str] | tuple[str, str, str, list[tuple[str, str]]]] = [
    (
        "call-non-callable",
        "test_ty98_fails_call_non_callable.py",
        """def f() -> None:
    x: int = 1
    x()
""",
    ),
    (
        "duplicate-base",
        "test_ty98_fails_duplicate_base.py",
        """class A:
    pass

class B(A, A):
    pass
""",
    ),
    (
        "invalid-assignment",
        "test_ty98_fails_invalid_assignment.py",
        """def f() -> None:
    x: int = "not an int"
""",
    ),
    (
        "subclass-of-final-class",
        "test_ty98_fails_subclass_of_final_class.py",
        """from typing import final

@final
class A:
    pass

class B(A):
    pass
""",
    ),
    (
        "missing-argument",
        "test_ty98_fails_missing_argument.py",
        """def g(a: int, b: int) -> int:
    return a + b

def f() -> None:
    g(1)
""",
    ),
    (
        "unknown-argument",
        "test_ty98_fails_unknown_argument.py",
        """def g(a: int) -> int:
    return a

def f() -> None:
    g(a=1, b=2)
""",
    ),
    (
        "invalid-argument-type",
        "test_ty98_fails_invalid_argument_type.py",
        """def func(x: int) -> None: ...

def f() -> None:
    func("foo")
""",
    ),
    (
        "abstract-method-in-final-class",
        "test_ty98_fails_abstract_method_in_final_class.py",
        """from abc import ABC, abstractmethod
from typing import final

class Base(ABC):
    @abstractmethod
    def method(self) -> int: ...

@final
class Derived(Base):
    pass
""",
    ),
    (
        "ambiguous-protocol-member",
        "test_ty98_fails_ambiguous_protocol_member.py",
        """from typing import Protocol

class BaseProto(Protocol):
    a: int
    c = "some variable"
""",
    ),
    (
        "assert-type-unspellable-subtype",
        "test_ty98_fails_assert_type_unspellable_subtype.py",
        """from typing import assert_type

def _(x: int) -> None:
    if x:
        assert_type(x, int)
""",
    ),
    (
        "byte-string-type-annotation",
        "test_ty98_fails_byte_string_type_annotation.py",
        """def test() -> b"int":
    ...
""",
    ),
    (
        "call-abstract-method",
        "test_ty98_fails_call_abstract_method.py",
        """from abc import ABC, abstractmethod

class Foo(ABC):
    @classmethod
    @abstractmethod
    def method(cls) -> int: ...

Foo.method()
""",
    ),
    (
        "call-top-callable",
        "test_ty98_fails_call_top_callable.py",
        """def f(x: object) -> None:
    if callable(x):
        x()
""",
    ),
    (
        "conflicting-declarations",
        "test_ty98_fails_conflicting_declarations.py",
        """def f(b: bool) -> None:
    if b:
        a: int
    else:
        a: str
    a = 1
""",
    ),
    (
        "conflicting-metaclass",
        "test_ty98_fails_conflicting_metaclass.py",
        """class M1(type): ...
class M2(type): ...
class A(metaclass=M1): ...
class B(metaclass=M2): ...

class C(A, B): ...
""",
    ),
    (
        "cyclic-type-alias-definition",
        "test_ty98_fails_cyclic_type_alias_definition.py",
        """type Itself = Itself
""",
    ),
    (
        "deprecated",
        "test_ty98_fails_deprecated.py",
        """import warnings

@warnings.deprecated("use new_func")
def old_func() -> None: ...

def f() -> None:
    old_func()
""",
    ),
    (
        "dataclass-field-order",
        "test_ty98_fails_dataclass_field_order.py",
        """from dataclasses import dataclass

@dataclass
class Example:
    x: int = 1
    y: str
""",
    ),
    (
        "division-by-zero",
        "test_ty98_fails_division_by_zero.py",
        """def f() -> int:
    return 5 / 0
""",
    ),
    (
        "duplicate-kw-only",
        "test_ty98_fails_duplicate_kw_only.py",
        """from dataclasses import KW_ONLY, dataclass

@dataclass
class A:
    b: int
    _1: KW_ONLY
    c: str
    _2: KW_ONLY
    d: bytes
""",
    ),
    (
        "empty-body",
        "test_ty98_fails_empty_body.py",
        """def foo() -> int: ...
""",
    ),
    (
        "escape-character-in-forward-annotation",
        "test_ty98_fails_escape_char_forward_annotation.py",
        """def foo() -> "intt\\\\b":
    return 0
""",
    ),
    (
        "final-without-value",
        "test_ty98_fails_final_without_value.py",
        """from typing import Final

MY_CONSTANT: Final[int]
""",
    ),
    (
        "fstring-type-annotation",
        "test_ty98_fails_fstring_type_annotation.py",
        """def test() -> f"int":
    ...
""",
    ),
    (
        "ignore-comment-unknown-rule",
        "test_ty98_fails_ignore_comment_unknown_rule.py",
        """def f() -> int:
    return 1  # ty: ignore[division-by-zer]
""",
    ),
    (
        "implicit-concatenated-string-type-annotation",
        "test_ty98_fails_implicit_concatenated_string_type_annotation.py",
        """def test() -> "Literal[" "5" "]":
    ...
""",
    ),
    (
        "inconsistent-mro",
        "test_ty98_fails_inconsistent_mro.py",
        """class A: ...
class B(A): ...

class C(A, B): ...
""",
    ),
    (
        "index-out-of-bounds",
        "test_ty98_fails_index_out_of_bounds.py",
        """def f() -> int:
    t = (0, 1, 2)
    return t[3]
""",
    ),
    (
        "ineffective-final",
        "test_ty98_fails_ineffective_final.py",
        """from typing import final

MyClass = final(type("MyClass", (), {}))
""",
    ),
    (
        "instance-layout-conflict",
        "test_ty98_fails_instance_layout_conflict.py",
        """class A:
    __slots__ = ("a", "b")

class B:
    __slots__ = ("a", "b")

class C(A, B): ...
""",
    ),
    (
        "invalid-await",
        "test_ty98_fails_invalid_await.py",
        """async def f() -> None:
    await 42
""",
    ),
    (
        "invalid-base",
        "test_ty98_fails_invalid_base.py",
        """class A(42): ...
""",
    ),
    (
        "invalid-context-manager",
        "test_ty98_fails_invalid_context_manager.py",
        """def f() -> None:
    with 1:
        pass
""",
    ),
    (
        "invalid-dataclass",
        "test_ty98_fails_invalid_dataclass.py",
        """from dataclasses import dataclass
from typing import NamedTuple

@dataclass
class Foo(NamedTuple):
    x: int
""",
    ),
    (
        "invalid-dataclass-override",
        "test_ty98_fails_invalid_dataclass_override.py",
        """from dataclasses import dataclass

@dataclass(frozen=True)
class A:
    def __setattr__(self, name: str, value: object) -> None: ...
""",
    ),
    (
        "invalid-declaration",
        "test_ty98_fails_invalid_declaration.py",
        """def f() -> None:
    a = 1
    a: str
""",
    ),
    (
        "invalid-exception-caught",
        "test_ty98_fails_invalid_exception_caught.py",
        """def f() -> None:
    try:
        1 / 0
    except 1:
        pass
""",
    ),
    (
        "invalid-explicit-override",
        "test_ty98_fails_invalid_explicit_override.py",
        """from typing import override

class C:
    @override
    def not_overriding(self) -> int:
        return 0
""",
    ),
    (
        "invalid-frozen-dataclass-subclass",
        "test_ty98_fails_invalid_frozen_dataclass_subclass.py",
        """from dataclasses import dataclass

@dataclass
class Base:
    x: int

@dataclass(frozen=True)
class Child(Base):
    y: int
""",
    ),
    (
        "invalid-generic-class",
        "test_ty98_fails_invalid_generic_class.py",
        """from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U", default=int)

class D(Generic[U, T]): ...
""",
    ),
    (
        "invalid-generic-enum",
        "test_ty98_fails_invalid_generic_enum.py",
        """from enum import Enum

class E[tuple](Enum):
    A = 1
""",
    ),
    (
        "invalid-ignore-comment",
        "test_ty98_fails_invalid_ignore_comment.py",
        """def f() -> int:
    return 1  # type: ignoree
""",
    ),
    (
        "invalid-key",
        "test_ty98_fails_invalid_key.py",
        """from typing import TypedDict

class Person(TypedDict):
    name: str
    age: int

def f() -> None:
    carol = Person(name="Carol", age=25, typo_key=0)
""",
    ),
    (
        "invalid-legacy-positional-parameter",
        "test_ty98_fails_invalid_legacy_positional_parameter.py",
        """def f(x: int, __y: int) -> int:
    return x + __y
""",
    ),
    (
        "invalid-legacy-type-variable",
        "test_ty98_fails_invalid_legacy_type_variable.py",
        """from typing import TypeVar

Q = TypeVar("S")
""",
    ),
    (
        "invalid-match-pattern",
        "test_ty98_fails_invalid_match_pattern.py",
        """NotAClass = 42

def f(x: object) -> None:
    match x:
        case NotAClass():
            pass
""",
    ),
    (
        "invalid-method-override",
        "test_ty98_fails_invalid_method_override.py",
        """class Base:
    def foo(self) -> int:
        return 0

class Sub(Base):
    def foo(self) -> str:
        return "x"
""",
    ),
    (
        "invalid-named-tuple",
        "test_ty98_fails_invalid_named_tuple.py",
        """from typing import NamedTuple

class Foo(NamedTuple, object):
    x: int
""",
    ),
    (
        "invalid-newtype",
        "test_ty98_fails_invalid_newtype.py",
        """from typing import NewType

Baz = NewType("Baz", int | str)
""",
    ),
    (
        "invalid-overload",
        "test_ty98_fails_invalid_overload.py",
        """from typing import overload

@overload
def foo(x: int) -> int: ...
@overload
def foo(x: str) -> str: ...
""",
    ),
    (
        "invalid-parameter-default",
        "test_ty98_fails_invalid_parameter_default.py",
        """def f(a: int = "") -> int:
    return a
""",
    ),
    (
        "invalid-paramspec",
        "test_ty98_fails_invalid_paramspec.py",
        """from typing import ParamSpec

P2 = ParamSpec("S2")
""",
    ),
    (
        "invalid-protocol",
        "test_ty98_fails_invalid_protocol.py",
        """from typing import Protocol

class Foo(int, Protocol): ...
""",
    ),
    (
        "invalid-raise",
        "test_ty98_fails_invalid_raise.py",
        """def f() -> None:
    raise "oops!"
""",
    ),
    (
        "invalid-return-type",
        "test_ty98_fails_invalid_return_type.py",
        """def func() -> int:
    return "a"
""",
    ),
    (
        "invalid-super-argument",
        "test_ty98_fails_invalid_super_argument.py",
        """class A: ...
class B(A): ...

def f() -> None:
    super(A(), B())
""",
    ),
    (
        "invalid-syntax-in-forward-annotation",
        "test_ty98_fails_invalid_syntax_in_forward_annotation.py",
        """def foo() -> "intstance of C":
    return 42

class C: ...
""",
    ),
    (
        "invalid-type-alias-type",
        "test_ty98_fails_invalid_type_alias_type.py",
        """from typing import TypeAliasType

def get_name() -> str:
    return "A"

NewAlias = TypeAliasType(get_name(), int)
""",
    ),
    (
        "invalid-total-ordering",
        "test_ty98_fails_invalid_total_ordering.py",
        """from functools import total_ordering

@total_ordering
class MyClass:
    def __eq__(self, other: object) -> bool:
        return True
""",
    ),
    (
        "invalid-type-checking-constant",
        "test_ty98_fails_invalid_type_checking_constant.py",
        """TYPE_CHECKING = ""
""",
    ),
    (
        "invalid-type-form",
        "test_ty98_fails_invalid_type_form.py",
        """def f() -> None:
    a: type[1] = int
""",
    ),
    (
        "invalid-type-guard-definition",
        "test_ty98_fails_invalid_type_guard_definition.py",
        """from typing import TypeIs

def f() -> TypeIs[int]: ...
""",
    ),
    (
        "invalid-type-variable-bound",
        "test_ty98_fails_invalid_type_variable_bound.py",
        """from typing import TypeVar

T = TypeVar("T", bound=list["T"])
""",
    ),
    (
        "invalid-type-variable-default",
        "test_ty98_fails_invalid_type_variable_default.py",
        """from typing import TypeVar

T = TypeVar("T", bound=str, default=int)
""",
    ),
    (
        "invalid-typed-dict-header",
        "test_ty98_fails_invalid_typed_dict_header.py",
        """from typing import TypedDict

class Meta(type): ...

class Foo(TypedDict, metaclass=Meta):
    x: int
""",
    ),
    (
        "invalid-typed-dict-statement",
        "test_ty98_fails_invalid_typed_dict_statement.py",
        """from typing import TypedDict

class Foo(TypedDict):
    def bar(self) -> None:
        pass
""",
    ),
    (
        "isinstance-against-protocol",
        "test_ty98_fails_isinstance_against_protocol.py",
        """from typing import Protocol

class HasX(Protocol):
    x: int

def f(arg: object) -> None:
    isinstance(arg, HasX)
""",
    ),
    (
        "isinstance-against-typed-dict",
        "test_ty98_fails_isinstance_against_typed_dict.py",
        """from typing import TypedDict

class Movie(TypedDict):
    name: str
    director: str

def f(arg: object) -> None:
    isinstance(arg, Movie)
""",
    ),
    (
        "missing-typed-dict-key",
        "test_ty98_fails_missing_typed_dict_key.py",
        """from typing import TypedDict

class Person(TypedDict):
    name: str
    age: int

alice: Person = {"name": "Alice"}
""",
    ),
    (
        "no-matching-overload",
        "test_ty98_fails_no_matching_overload.py",
        """from typing import overload

@overload
def func(x: int) -> int: ...
@overload
def func(x: bool) -> int: ...
def func(x: int | bool) -> int:
    return 0

def f() -> None:
    func("string")
""",
    ),
    (
        "not-iterable",
        "test_ty98_fails_not_iterable.py",
        """def f() -> None:
    for i in 34:
        pass
""",
    ),
    (
        "not-subscriptable",
        "test_ty98_fails_not_subscriptable.py",
        """def f() -> None:
    x = 4[1]
""",
    ),
    (
        "override-of-final-method",
        "test_ty98_fails_override_of_final_method.py",
        """from typing import final

class A:
    @final
    def foo(self) -> int:
        return 0

class B(A):
    def foo(self) -> int:
        return 1
""",
    ),
    (
        "override-of-final-variable",
        "test_ty98_fails_override_of_final_variable.py",
        """from typing import Final

class A:
    X: Final[int] = 1

class B(A):
    X = 2
""",
    ),
    (
        "parameter-already-assigned",
        "test_ty98_fails_parameter_already_assigned.py",
        """def f(x: int) -> int:
    return x

def g() -> None:
    f(1, x=2)
""",
    ),
    (
        "possibly-unresolved-reference",
        "test_ty98_fails_possibly_unresolved_reference.py",
        """def f() -> None:
    for i in range(0):
        x = i
    print(x)
""",
    ),
    (
        "positional-only-parameter-as-kwarg",
        "test_ty98_fails_positional_only_parameter_as_kwarg.py",
        """def f(x: int, /) -> int:
    return x

def g() -> None:
    f(x=1)
""",
    ),
    (
        "raw-string-type-annotation",
        "test_ty98_fails_raw_string_type_annotation.py",
        """def test() -> r"int":
    ...
""",
    ),
    (
        "redundant-cast",
        "test_ty98_fails_redundant_cast.py",
        """from typing import cast

def example(x: int) -> int:
    return cast(int, x)
""",
    ),
    (
        "redundant-final-classvar",
        "test_ty98_fails_redundant_final_classvar.py",
        """from typing import ClassVar, Final

class C:
    x: ClassVar[Final[int]] = 1
""",
    ),
    (
        "super-call-in-named-tuple-method",
        "test_ty98_fails_super_call_in_named_tuple_method.py",
        """from typing import NamedTuple

class F(NamedTuple):
    x: int

    def method(self) -> None:
        super()
""",
    ),
    (
        "too-many-positional-arguments",
        "test_ty98_fails_too_many_positional_arguments.py",
        """def f() -> None: ...

def g() -> None:
    f("foo")
""",
    ),
    (
        "type-assertion-failure",
        "test_ty98_fails_type_assertion_failure.py",
        """from typing import assert_type

def f(x: int) -> None:
    assert_type(x, str)
""",
    ),
    (
        "unavailable-implicit-super-arguments",
        "test_ty98_fails_unavailable_implicit_super_arguments.py",
        """super()
""",
    ),
    (
        "undefined-reveal",
        "test_ty98_fails_undefined_reveal.py",
        """def f(x: int) -> None:
    reveal_type(x)
""",
    ),
    (
        "unresolved-attribute",
        "test_ty98_fails_unresolved_attribute.py",
        """class A: ...

def f() -> None:
    A().foo
""",
    ),
    (
        "unresolved-global",
        "test_ty98_fails_unresolved_global.py",
        """def f() -> None:
    global x
    x = 42
""",
    ),
    (
        "unresolved-import",
        "test_ty98_fails_unresolved_import.py",
        """from nonexistent_module_ty98_xyz import X

def use(x: X) -> None:
    return
""",
    ),
    (
        "unresolved-reference",
        "test_ty98_fails_unresolved_reference.py",
        """def bad() -> int:
    return missing_name
""",
    ),
    (
        "unsupported-dynamic-base",
        "test_ty98_fails_unsupported_dynamic_base.py",
        """class Base: ...

def factory(base: type[Base]) -> type:
    return type("Dynamic", (base,), {})

class D(factory(Base)): ...
""",
    ),
    (
        "unsupported-base",
        "test_ty98_fails_unsupported_base.py",
        """import datetime

class A: ...
class B: ...

if datetime.date.today().weekday() != 6:
    C = A
else:
    C = B

class D(C): ...
""",
    ),
    (
        "unused-ignore-comment",
        "test_ty98_fails_unused_ignore_comment.py",
        """def f() -> int:
    return 20 / 2  # ty: ignore[division-by-zero]
""",
    ),
    (
        "unused-type-ignore-comment",
        "test_ty98_fails_unused_type_ignore_comment.py",
        """def f() -> int:
    return 1  # type: ignore[redundant-cast]
""",
    ),
    (
        "useless-overload-body",
        "test_ty98_fails_useless_overload_body.py",
        """from typing import overload

@overload
def foo(x: int) -> int:
    return x + 1

def foo(x: int | str) -> int | str:
    return x
""",
    ),
    (
        "static-assert-error",
        "test_ty98_fails_static_assert_error.py",
        """from ty_extensions import static_assert

static_assert(1 + 1 == 3)
""",
    ),
    (
        "possibly-missing-import",
        "test_ty98_fails_possibly_missing_import.py",
        """from ty98_conditional_module import a


def use() -> int:
    return a
""",
        [
            (
                "ty98_conditional_module.py",
                """import datetime


if datetime.date.today().weekday() != 6:
    a = 1
""",
            )
        ],
    ),
]


@pytest.mark.usefixtures(
    "mock_lightweight_project", "mock_lightweight_project_on_feature_branch"
)
def test_all_ty_rules_flagged_in_type_check_output(
    default_command_context: FeatureTestCommandContext,
) -> None:
    """Type check fails and each ty rule is reported in the output."""
    test_dir = get_python_subproject(
        project_root=default_command_context.mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir()
    entry_with_extras_len = 4  # (rule, file_name, file_contents, extra_files)
    for entry in TY_RULES:
        file_name = entry[1]
        file_contents = entry[2]
        test_dir.joinpath(file_name).write_text(file_contents)
        if len(entry) == entry_with_extras_len:
            entry_with_extras = cast(tuple[str, str, str, list[tuple[str, str]]], entry)
            for extra_name, extra_content in entry_with_extras[3]:
                test_dir.joinpath(extra_name).write_text(extra_content)
    default_command_context.expect_failure = True
    return_code, stdout, stderr = run_command_and_save_logs(
        context=default_command_context, command_args=["type_check_pypi"]
    )
    assert return_code != 0, "type_check_pypi should fail when rules are violated"
    combined_output = stdout + stderr
    # Ty prints rule names in brackets, e.g. [invalid-return-type]
    found_rules = set(re.findall(r"\[([a-z][a-z0-9-]+)\]", combined_output))
    expected_rules = {entry[0] for entry in TY_RULES}
    missing = expected_rules - found_rules
    assert not missing, (
        f"Rules not flagged in type checker output: {sorted(missing)}. "
        "Check that each rule is triggered by its test file."
    )
