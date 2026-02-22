from collections.abc import Callable
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest
from test_utils.command_runner import run_command_and_save_logs

from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
)


@pytest.fixture
def type_check_pypi_return_code(
    request: SubRequest,
    mock_project_root: Path,
    ticket_branch_make_command_prefix: list[str],
    real_project_root_dir: Path,
) -> Callable[[], int]:
    def _run_type_check() -> int:
        return_code, _, _ = run_command_and_save_logs(
            args=[*ticket_branch_make_command_prefix, "type_check_pypi"],
            cwd=mock_project_root,
            test_name=request.node.name,
            real_project_root_dir=real_project_root_dir,
        )
        return return_code

    return _run_type_check


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_passes_no_issues(type_check_pypi_return_code: Callable[[], int]) -> None:
    # Default state - should pass as long as style checks are passing for the repo
    assert type_check_pypi_return_code() == 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_type_arg(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_type_arg.py").write_text(
        '''def some_function(items: list) -> list:
    """func docstring"""
    return items
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_no_untyped_def(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_no_untyped_def.py").write_text(
        '''def some_function(items) -> list:
    """func docstring"""
    return items
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_redundant_cast(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_redundant_cast.py").write_text(
        '''def example(x: Count) -> int:
    """func docstring"""
    return cast(int, x)
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_redundant_self(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_redundant_self.py").write_text(
        '''def copy(self: Self) -> Self:
    """func docstring"""
    return type(self)()
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_comparison_overlap(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_comparison_overlap.py").write_text(
        '''def is_magic(x: bytes) -> bool:
    """func docstring"""
    return x == 'magic'
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_no_untyped_call(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_no_untyped_call.py").write_text(
        '''def do_it() -> None:
    """func docstring"""
    bad()

def bad():
    """docstring"""
    return
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_no_any_return(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_no_any_return.py").write_text(
        '''def some_function(x: dict[str, Any]) -> str:
    """func docstring"""
    return x['str']
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_no_any_unimported(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_no_any_unimported.py").write_text(
        '''from animals import Cat


def feed(cat: Cat) -> None:
    """func docstring"""
    return
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_redundant_expr(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_redundant_expr.py").write_text(
        '''def example(x: int) -> int:
    """func docstring"""
    if isinstance(x, int) and x > 0:
        return 1
    else:
        return 0
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_possibly_undefined(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_possibly_undefined.py").write_text(
        '''def some_function(val: int, flag: bool) -> int:
    """func docstring"""
    if flag:
        a = 12
    return val + a
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_truthy_bool(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_truthy_bool.py").write_text(
        """class Foo:
    pass
foo = Foo()

if foo:
    a = 0
"""
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_truthy_iterable(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_truthy_iterable.py").write_text(
        '''from typing import Iterable

def transform(items: Iterable[int]) -> list[int]:
    """func docstring"""
    if not items:
        return [42]
    return [x + 1 for x in items]
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_ignore_without_code(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_ignore_without_code.py").write_text(
        '''def some_function(items: list) -> list:  # type: ignore
    """func docstring"""
    return items
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_unused_awaitable(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_unused_awaitable.py").write_text(
        """import asyncio

async def f() -> int:
    return 0

async def g() -> None:
    asyncio.create_task(f())
"""
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_unused_ignore(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_unused_ignore.py").write_text(
        '''def add(a: int, b: int) -> int:
    """func docstring"""
    return a + b  # type: ignore[unused-awaitable]
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_explicit_override(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_explicit_override.py").write_text(
        '''from typing import override

class Parent:
    def f(self, x: int) -> None:
    """func docstring"""
        pass

    def g(self, y: int) -> None:
    """func docstring"""
        pass


class Child(Parent):
    def f(self, x: int) -> None:  # Error: Missing @override decorator
    """func docstring"""
        pass

    @override
    def g(self, y: int) -> None:
    """func docstring"""
        pass
'''
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_mutable_override(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_mutable_override.py").write_text(
        """from typing import Any

class C:
    x: float
    y: float
    z: float

class D(C):
    x: int  # Error: Covariant override of a mutable attribute
            # (base class "C" defined the type as "float",
            # expression has type "int")  [mutable-override]
    y: float  # OK
    z: Any  # OK
"""
    )
    assert type_check_pypi_return_code() != 0


@pytest.mark.usefixtures("mock_lightweight_project")
def test_mypy_fails_unimported_reveal(
    mock_project_root: Path, type_check_pypi_return_code: Callable[[], int]
) -> None:
    # Putting "bad" file in test avoids additional src style enforcement
    get_python_subproject(
        project_root=mock_project_root,
        subproject_context=SubprojectContext.PYPI,
    ).get_test_dir().joinpath("test_mypy_fails_unimported_reveal.py").write_text(
        """x = 1
reveal_type(x)
"""
    )
    assert type_check_pypi_return_code() != 0
