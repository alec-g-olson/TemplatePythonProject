from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
    get_python_subproject,
)
from build_support.file_caching import FileCacheEngine, FileCacheInfo, TestFileInfo


@pytest.mark.parametrize(
    argnames="file_info",
    argvalues=[
        TestFileInfo(
            file_path=Path("some/file"),
            tests_passed=datetime(2024, 3, 30, 17, 16, 23, 163489, tzinfo=UTC),
        ),
        TestFileInfo(file_path=Path("some/other/file"), tests_passed=None),
    ],
)
def test_file_info_serialize_deserialize(file_info: TestFileInfo) -> None:
    dump = file_info.model_dump(mode="json")
    read = TestFileInfo.model_validate(dump)
    assert read == file_info


def test_file_info_serialize_deserialize_bad_file_path() -> None:
    with pytest.raises(ValidationError):
        TestFileInfo(file_path=4, tests_passed=None)


def test_file_info_serialize_deserialize_bad_datetime() -> None:
    with pytest.raises(ValidationError):
        TestFileInfo(file_path=Path("some/file"), tests_passed="5/1/2025")


@pytest.fixture
def file_cache_data_dict() -> dict[str, Any]:
    return {
        "subproject_context": "build_support",
        "test_cache_info": [
            {"file_path": "some/file", "tests_passed": "2024-03-30T17:16:23.163489Z"},
            {"file_path": "some/other/file", "tests_passed": None},
        ],
    }


@pytest.fixture
def file_cache_yaml_str(file_cache_data_dict: dict[str, Any]) -> str:
    return yaml.dump(file_cache_data_dict)


def test_load(file_cache_yaml_str: str, file_cache_data_dict: dict[str, Any]) -> None:
    file_cache_info = FileCacheInfo.from_yaml(yaml_str=file_cache_yaml_str)
    assert file_cache_info == FileCacheInfo.model_validate(file_cache_data_dict)


def test_load_bad_subproject_context(file_cache_data_dict: dict[str, Any]) -> None:
    file_cache_data_dict["subproject_context"] = 4
    checksum_cache_yaml_str = yaml.dump(file_cache_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_test_cache_info(file_cache_data_dict: dict[str, Any]) -> None:
    file_cache_data_dict["test_cache_info"] = 4
    checksum_cache_yaml_str = yaml.dump(file_cache_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_dump(file_cache_yaml_str: str, file_cache_data_dict: dict[str, Any]) -> None:
    file_cache_info = FileCacheInfo.model_validate(file_cache_data_dict)
    assert file_cache_info.to_yaml() == file_cache_yaml_str


def test_get_file_cache_for(
    mock_project_root: Path, subproject_context: SubprojectContext
) -> None:
    file_cache_info = FileCacheInfo.get_file_cache_for(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert file_cache_info == FileCacheInfo(subproject_context=subproject_context)
    test_file_info = TestFileInfo(
        file_path=Path("some/file"), tests_passed=datetime.now(tz=UTC)
    )
    file_cache_info.test_cache_info.append(test_file_info)
    get_python_subproject(
        subproject_context=subproject_context, project_root=mock_project_root
    ).get_file_cache_yaml().write_text(file_cache_info.to_yaml())
    new_file_cache_info = FileCacheInfo.get_file_cache_for(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert new_file_cache_info == file_cache_info


@pytest.fixture
def file_cache_engine(mock_project_root: Path) -> FileCacheEngine:
    return FileCacheEngine(
        subproject_context=SubprojectContext.BUILD_SUPPORT,
        project_root=mock_project_root,
    )


def test_write_text(file_cache_engine: FileCacheEngine) -> None:
    expected_location = file_cache_engine.subproject.get_file_cache_yaml()
    test_files = [Path("some/file"), Path("some/other/file")]
    for test_file in test_files:
        file_cache_engine.update_test_pass_timestamp(file_path=test_file)
        file_cache_engine.update_test_pass_timestamp(file_path=test_file)
    assert not expected_location.exists()
    assert len(file_cache_engine.cache_data.test_cache_info) == len(test_files)
    file_cache_engine.write_text()
    written_cache_info = FileCacheInfo.from_yaml(expected_location.read_text())
    assert written_cache_info == file_cache_engine.cache_data


def test_get_last_modified_time(tmp_path: Path) -> None:
    file_path = tmp_path.joinpath("path", "to", "a_file")
    assert not file_path.exists()
    with pytest.raises(FileNotFoundError):
        FileCacheEngine.get_last_modified_time(file_path=file_path)
    time_before_write = datetime.now(tz=UTC)
    sleep(0.001)
    file_path.parent.mkdir(parents=True)
    file_path.write_text("some contents")
    time_after_write = datetime.now(tz=UTC)
    mtime = FileCacheEngine.get_last_modified_time(file_path=file_path)
    assert time_before_write <= mtime <= time_after_write


def test_most_recent_conftest_update(file_cache_engine: FileCacheEngine) -> None:
    top_test_folder = file_cache_engine.subproject.get_test_dir()
    deep_test_folder = top_test_folder.joinpath("a", "b", "c")
    deep_test_folder.mkdir(parents=True)
    # If not conftests report min datetime
    no_conftest_datetime = file_cache_engine.most_recent_conftest_update(
        test_dir=top_test_folder
    )
    assert no_conftest_datetime == datetime.min.replace(tzinfo=UTC)
    assert no_conftest_datetime == file_cache_engine.most_recent_conftest_update(
        test_dir=deep_test_folder
    )
    # Make some conftests, and since top is made second, they should have the same
    # last modified result
    deep_conftest = deep_test_folder.joinpath("conftest.py")
    deep_conftest.touch()
    top_conftest = top_test_folder.joinpath("conftest.py")
    top_conftest.touch()
    unmodified_conftest_datetime = file_cache_engine.most_recent_conftest_update(
        test_dir=top_test_folder
    )
    assert (
        unmodified_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(test_dir=deep_test_folder)
    )
    assert unmodified_conftest_datetime > no_conftest_datetime
    # Wait a beat and update the top level conftest.  This will change the result of
    # both folders' conftest update
    sleep(0.001)
    top_conftest.write_text("some new content")
    modified_top_conftest_datetime = file_cache_engine.most_recent_conftest_update(
        test_dir=top_test_folder
    )
    assert (
        modified_top_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(test_dir=deep_test_folder)
    )
    assert modified_top_conftest_datetime > unmodified_conftest_datetime
    # Wait a beat and update the deep conftest.  This should only change the result of
    # the deep folder's conftest update
    sleep(0.001)
    deep_conftest.write_text("some new content")
    modified_deep_conftest_datetime = file_cache_engine.most_recent_conftest_update(
        test_dir=deep_test_folder
    )
    assert (
        modified_top_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(test_dir=top_test_folder)
    )
    assert modified_deep_conftest_datetime > modified_top_conftest_datetime
    # Check a folder without a conftest. Should be the same as the top level.
    intermediate_test_folder = deep_test_folder.parent
    assert (
        modified_top_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(
            test_dir=intermediate_test_folder
        )
    )
    # Wait a beat and add a conftest to this level.  Should update deep result but not
    # top level result
    sleep(0.001)
    intermediate_conftest = intermediate_test_folder.joinpath("conftest.py")
    intermediate_conftest.touch()
    modified_intermediate_conftest_datetime = (
        file_cache_engine.most_recent_conftest_update(test_dir=intermediate_test_folder)
    )
    assert modified_intermediate_conftest_datetime > modified_deep_conftest_datetime
    assert (
        modified_intermediate_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(test_dir=deep_test_folder)
    )
    assert (
        modified_top_conftest_datetime
        == file_cache_engine.most_recent_conftest_update(test_dir=top_test_folder)
    )


def test_most_recent_src_file_update(file_cache_engine: FileCacheEngine) -> None:
    pypi_package_folder = file_cache_engine.subproject.get_python_package_dir()
    sub_folder = pypi_package_folder.joinpath("a")
    sub_folder.mkdir(parents=True)
    no_conftest_datetime = file_cache_engine.most_recent_src_file_update()
    assert no_conftest_datetime == datetime.min.replace(tzinfo=UTC)
    # populate_folders
    file_1 = pypi_package_folder.joinpath("file_1.py")
    file_2 = pypi_package_folder.joinpath("file_2.py")
    file_3 = sub_folder.joinpath("file_3.py")
    file_1.touch()
    file_2.touch()
    file_3.touch()
    files_exist_datetime = file_cache_engine.most_recent_src_file_update()
    assert files_exist_datetime > no_conftest_datetime
    sleep(0.001)
    # add a file
    file_4 = sub_folder.joinpath("file_4.py")
    file_4.touch()
    file_added_datetime = file_cache_engine.most_recent_src_file_update()
    assert file_added_datetime > files_exist_datetime
    sleep(0.001)
    # check after waiting a bit without changes
    file_added_datetime_round_2 = file_cache_engine.most_recent_src_file_update()
    assert file_added_datetime_round_2 == file_added_datetime
    sleep(0.001)
    # update a file
    file_1.write_text("some new content")
    file_added_datetime = file_cache_engine.most_recent_src_file_update()
    assert file_added_datetime > files_exist_datetime


def test_update_test_pass_timestamp(file_cache_engine: FileCacheEngine) -> None:
    test_file = file_cache_engine.subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.UNIT_TESTS
    ).joinpath("test_file.py")
    test_file.parent.mkdir(parents=True)
    test_file.touch()
    assert file_cache_engine.get_test_info_for_file(test_file) == TestFileInfo(
        file_path=test_file, tests_passed=None
    )
    datetime_to_use = datetime.now(tz=UTC)
    with patch("build_support.file_caching.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime_to_use
        file_cache_engine.update_test_pass_timestamp(file_path=test_file)
    assert file_cache_engine.get_test_info_for_file(test_file) == TestFileInfo(
        file_path=test_file, tests_passed=datetime_to_use
    )


def test_get_most_recent_file_update_in_dir_nonexistent(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    result = FileCacheEngine.get_most_recent_file_update_in_dir(directory=non_existent)
    assert result == datetime.min.replace(tzinfo=UTC)


def test_get_most_recent_file_update_in_dir_empty(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    result = FileCacheEngine.get_most_recent_file_update_in_dir(directory=empty_dir)
    assert result == datetime.min.replace(tzinfo=UTC)


def test_get_most_recent_file_update_in_dir_with_files(tmp_path: Path) -> None:
    resource_dir = tmp_path / "resources"
    resource_dir.mkdir()
    file_a = resource_dir / "a.txt"
    file_a.write_text("aaa")
    sleep(0.001)
    file_b = resource_dir / "b.txt"
    file_b.write_text("bbb")
    result = FileCacheEngine.get_most_recent_file_update_in_dir(directory=resource_dir)
    expected = FileCacheEngine.get_last_modified_time(file_path=file_b)
    assert result == expected


def test_get_most_recent_file_update_in_dir_nested(tmp_path: Path) -> None:
    resource_dir = tmp_path / "resources"
    resource_dir.mkdir()
    sub_dir = resource_dir / "sub"
    sub_dir.mkdir()
    file_a = resource_dir / "a.txt"
    file_a.write_text("aaa")
    sleep(0.001)
    nested_file = sub_dir / "nested.txt"
    nested_file.write_text("nested")
    result = FileCacheEngine.get_most_recent_file_update_in_dir(directory=resource_dir)
    expected = FileCacheEngine.get_last_modified_time(file_path=nested_file)
    assert result == expected
