from pathlib import Path
from time import sleep
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)
from build_support.file_caching import (
    FileCacheEngine,
    FileCacheInfo,
    UnitTestInfo,
    get_corresponding_unit_test_folder_for_src_folder,
)


@pytest.fixture()
def file_checksum_data_dict() -> dict[str, Any]:
    return {
        "subproject_context": "build_support",
        "cache_info": {
            "some/file": "2024-03-30T17:16:23.163489+00:00",
            "some/other/file": "2024-03-30T17:17:01.368095+00:00",
        },
    }


@pytest.fixture()
def checksum_cache_yaml_str(file_checksum_data_dict: dict[str, Any]) -> str:
    return yaml.dump(file_checksum_data_dict)


def test_load(
    checksum_cache_yaml_str: str, file_checksum_data_dict: dict[str, Any]
) -> None:
    file_cache_info = FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)
    assert file_cache_info == FileCacheInfo.model_validate(file_checksum_data_dict)


def test_load_bad_subproject_context(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["subproject_context"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_cache_info(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["cache_info"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_cache_info_key(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["cache_info"][4] = "2024-03-30T17:17:20.985351+00:00"
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_cache_info_value(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["cache_info"]["some/third/file"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_dump(
    checksum_cache_yaml_str: str, file_checksum_data_dict: dict[str, Any]
) -> None:
    file_cache_info = FileCacheInfo.model_validate(file_checksum_data_dict)
    assert file_cache_info.to_yaml() == checksum_cache_yaml_str


@pytest.fixture()
def file_in_subproject(mock_subproject: PythonSubproject) -> Path:
    new_file = mock_subproject.get_src_dir().joinpath("path", "to", "a_file")
    new_file.parent.mkdir(parents=True)
    return new_file


@pytest.fixture()
def file_cache_engine(
    mock_project_root: Path, subproject_context: SubprojectContext
) -> FileCacheEngine:
    return FileCacheEngine(
        subproject_context=subproject_context, project_root=mock_project_root
    )


def test_engine_check_on_new_file(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("some contents")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)


def test_check_on_file_same(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)
    assert not file_cache_engine.file_has_been_changed(file_path=file_in_subproject)


def test_check_on_file_same_dump_and_read_cache(
    file_cache_engine: FileCacheEngine,
    file_in_subproject: Path,
    mock_project_root: Path,
    subproject_context: SubprojectContext,
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)
    file_cache_engine.write_text()
    new_file_cache_engine = FileCacheEngine(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert not new_file_cache_engine.file_has_been_changed(file_path=file_in_subproject)


def test_check_on_file_different(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)
    sleep(0.01)
    file_in_subproject.write_text("A file now has new contents!!!! Very shocking.")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)


def test_check_on_file_different_dump_and_read_cache(
    file_cache_engine: FileCacheEngine,
    file_in_subproject: Path,
    mock_project_root: Path,
    subproject_context: SubprojectContext,
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine.file_has_been_changed(file_path=file_in_subproject)
    file_cache_engine.write_text()
    sleep(0.01)
    file_in_subproject.write_text("A file now has new contents!!!! Very shocking.")
    new_file_cache_engine = FileCacheEngine(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert new_file_cache_engine.file_has_been_changed(file_path=file_in_subproject)


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_unit_test_info(
    file_cache_engine: FileCacheEngine, mock_subproject: PythonSubproject
) -> None:
    relative_src_files_to_create = [
        ["file1.py"],
        ["file2.py"],
        ["some_misplaced_src_file.txt"],
        ["__init__.py"],
        ["a", "file3.py"],
        ["a", "file4.py"],
        ["a", "file5.py"],
        ["a", "__init__.py"],
        ["a", "b", "file1.py"],
        ["a", "b", "file2.py"],
        ["a", "b", "__init__.py"],
        ["a", "c", "file1.py"],
        ["a", "c", "file2.py"],
        ["a", "c", "__init__.py"],
        ["a", "d", "__init__.py"],
        ["a", "d", "e", "some_file.py"],
        ["a", "d", "e", "__init__.py"],
        ["a", "f", "__init__.py"],
    ]
    python_pkg_root_dir = mock_subproject.get_python_package_dir()
    unit_test_root_dir = mock_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    test_folder_added = set()
    for relative_src_file_to_create in sorted(relative_src_files_to_create):
        src_file = python_pkg_root_dir.joinpath(*relative_src_file_to_create)
        src_folder = src_file.parent
        src_folder.mkdir(parents=True, exist_ok=True)
        src_file.touch()
        test_folder = get_corresponding_unit_test_folder_for_src_folder(
            python_pkg_root_dir=python_pkg_root_dir,
            unit_test_root_dir=unit_test_root_dir,
            src_folder_path=src_folder,
        )
        if src_file.name.endswith(".py") and src_file.name not in "__init__.py":
            if test_folder not in test_folder_added:
                test_folder.mkdir(parents=True, exist_ok=True)
                if test_folder.name in ("a", "b", "e"):
                    test_folder.joinpath("conftest.py").touch()
                test_folder_added.add(test_folder)
            test_folder.joinpath(f"test_{src_file.name}").touch()
    expected_unit_test_info = [
        UnitTestInfo(
            conftest_or_parent_conftest_was_updated=False,
            maybe_conftest_path=None,
            src_test_file_pairs=[
                (
                    python_pkg_root_dir.joinpath("file1.py"),
                    unit_test_root_dir.joinpath("test_file1.py"),
                ),
                (
                    python_pkg_root_dir.joinpath("file2.py"),
                    unit_test_root_dir.joinpath("test_file2.py"),
                ),
            ],
        ),
        UnitTestInfo(
            conftest_or_parent_conftest_was_updated=True,
            maybe_conftest_path=unit_test_root_dir.joinpath("a", "conftest.py"),
            src_test_file_pairs=[
                (
                    python_pkg_root_dir.joinpath("a", "file3.py"),
                    unit_test_root_dir.joinpath("a", "test_file3.py"),
                ),
                (
                    python_pkg_root_dir.joinpath("a", "file4.py"),
                    unit_test_root_dir.joinpath("a", "test_file4.py"),
                ),
                (
                    python_pkg_root_dir.joinpath("a", "file5.py"),
                    unit_test_root_dir.joinpath("a", "test_file5.py"),
                ),
            ],
        ),
        UnitTestInfo(
            conftest_or_parent_conftest_was_updated=True,
            maybe_conftest_path=unit_test_root_dir.joinpath("a", "b", "conftest.py"),
            src_test_file_pairs=[
                (
                    python_pkg_root_dir.joinpath("a", "b", "file1.py"),
                    unit_test_root_dir.joinpath("a", "b", "test_file1.py"),
                ),
                (
                    python_pkg_root_dir.joinpath("a", "b", "file2.py"),
                    unit_test_root_dir.joinpath("a", "b", "test_file2.py"),
                ),
            ],
        ),
        UnitTestInfo(
            conftest_or_parent_conftest_was_updated=True,
            maybe_conftest_path=None,
            src_test_file_pairs=[
                (
                    python_pkg_root_dir.joinpath("a", "c", "file1.py"),
                    unit_test_root_dir.joinpath("a", "c", "test_file1.py"),
                ),
                (
                    python_pkg_root_dir.joinpath("a", "c", "file2.py"),
                    unit_test_root_dir.joinpath("a", "c", "test_file2.py"),
                ),
            ],
        ),
        UnitTestInfo(
            conftest_or_parent_conftest_was_updated=True,
            maybe_conftest_path=unit_test_root_dir.joinpath(
                "a", "d", "e", "conftest.py"
            ),
            src_test_file_pairs=[
                (
                    python_pkg_root_dir.joinpath("a", "d", "e", "some_file.py"),
                    unit_test_root_dir.joinpath("a", "d", "e", "test_some_file.py"),
                ),
            ],
        ),
    ]
    assert list(file_cache_engine.get_unit_test_info()) == expected_unit_test_info


def test_get_corresponding_unit_test_folder_for_src_folder(
    mock_subproject: PythonSubproject,
) -> None:
    relative_path = ["path", "to", "a", "subfolder"]
    python_src_root_dir = mock_subproject.get_src_dir()
    src_folder = python_src_root_dir.joinpath(*relative_path)
    unit_test_root_dir = mock_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    )
    expected_test_folder = unit_test_root_dir.joinpath(*relative_path)
    assert (
        get_corresponding_unit_test_folder_for_src_folder(
            python_pkg_root_dir=python_src_root_dir,
            unit_test_root_dir=unit_test_root_dir,
            src_folder_path=src_folder,
        )
        == expected_test_folder
    )
