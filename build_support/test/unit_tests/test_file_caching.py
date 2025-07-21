from pathlib import Path
from time import sleep
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from build_support.ci_cd_vars.subproject_structure import (
    PythonSubproject,
    SubprojectContext,
)
from build_support.file_caching import (
    FileCacheEngine,
    FileCacheInfo,
)


@pytest.fixture
def file_checksum_data_dict() -> dict[str, Any]:
    return {
        "subproject_context": "build_support",
        "src_file_cache_info": {
            "src/file1.py": "2024-03-30T17:15:00.000000+00:00",
            "src/file2.py": "2024-03-30T17:15:30.000000+00:00",
        },
        "conftest_cache_info": {
            "test/conftest.py": "2024-03-30T17:14:00.000000+00:00",
            "test/unit_tests/conftest.py": "2024-03-30T17:14:30.000000+00:00",
        },
        "unit_test_cache_info": {
            "some/file": "2024-03-30T17:16:23.163489+00:00",
            "some/other/file": "2024-03-30T17:17:01.368095+00:00",
        },
        "unit_test_pass_info": {
            "some/file": "2024-03-30T17:18:00.000000+00:00",
            "some/other/file": "2024-03-30T17:18:30.000000+00:00",
        },
        "feature_test_cache_info": {
            "conftest": "2024-10-18T15:59:08.485987+00:00",
            "some/other/conftest": "2024-10-18T15:59:33.811010+00:00",
            "some/third/file": "2024-10-18T15:59:43.952650+00:00",
        },
        "feature_test_pass_info": {
            "conftest": "2024-10-18T16:00:00.000000+00:00",
            "some/other/conftest": "2024-10-18T16:00:30.000000+00:00",
            "some/third/file": "2024-10-18T16:01:00.000000+00:00",
        },
    }


@pytest.fixture
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


def test_load_bad_unit_test_cache_info(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["unit_test_cache_info"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_feature_test_cache_info(
    file_checksum_data_dict: dict[str, Any],
) -> None:
    file_checksum_data_dict["feature_test_cache_info"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_unit_test_cache_info_key(
    file_checksum_data_dict: dict[str, Any],
) -> None:
    file_checksum_data_dict["unit_test_cache_info"][4] = (
        "2024-03-30T17:17:20.985351+00:00"
    )
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_feature_test_cache_info_key(
    file_checksum_data_dict: dict[str, Any],
) -> None:
    file_checksum_data_dict["feature_test_cache_info"][4] = (
        "2024-03-30T17:17:20.985351+00:00"
    )
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_unit_test_cache_info_value(
    file_checksum_data_dict: dict[str, Any],
) -> None:
    file_checksum_data_dict["unit_test_cache_info"]["some/third/file"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_load_bad_feature_test_cache_info_value(
    file_checksum_data_dict: dict[str, Any],
) -> None:
    file_checksum_data_dict["feature_test_cache_info"]["some/fourth/file"] = 4
    checksum_cache_yaml_str = yaml.dump(file_checksum_data_dict)
    with pytest.raises(ValidationError):
        FileCacheInfo.from_yaml(yaml_str=checksum_cache_yaml_str)


def test_dump(
    checksum_cache_yaml_str: str, file_checksum_data_dict: dict[str, Any]
) -> None:
    file_cache_info = FileCacheInfo.model_validate(file_checksum_data_dict)
    assert file_cache_info.to_yaml() == checksum_cache_yaml_str


@pytest.fixture
def file_in_subproject(mock_subproject: PythonSubproject) -> Path:
    new_file = mock_subproject.get_src_dir().joinpath("path", "to", "a_file")
    new_file.parent.mkdir(parents=True)
    return new_file


@pytest.fixture
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
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_check_on_file_same(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    file_cache_engine.update_file_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    assert not file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_check_on_file_same_dump_and_read_cache(
    file_cache_engine: FileCacheEngine,
    file_in_subproject: Path,
    mock_project_root: Path,
    subproject_context: SubprojectContext,
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    file_cache_engine.update_file_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    assert not file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    file_cache_engine.write_text()
    new_file_cache_engine = FileCacheEngine(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert not new_file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_check_on_file_different(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    sleep(0.01)
    file_in_subproject.write_text("A file now has new contents!!!! Very shocking.")
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_check_on_file_different_dump_and_read_cache(
    file_cache_engine: FileCacheEngine,
    file_in_subproject: Path,
    mock_project_root: Path,
    subproject_context: SubprojectContext,
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    file_cache_engine.write_text()
    sleep(0.01)
    file_in_subproject.write_text("A file now has new contents!!!! Very shocking.")
    new_file_cache_engine = FileCacheEngine(
        subproject_context=subproject_context, project_root=mock_project_root
    )
    assert new_file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_update_file_timestamp(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    assert file_in_subproject not in file_cache_engine.cache_data.unit_test_cache_info
    file_cache_engine.update_file_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
    assert not file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )


def test_update_src_file_timestamp(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a source file!")
    assert file_in_subproject not in file_cache_engine.cache_data.src_file_cache_info
    file_cache_engine.update_file_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
    )
    assert not file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.SRC_FILE,
    )


def test_update_test_pass_timestamp(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a test file!")
    assert file_in_subproject not in file_cache_engine.cache_data.unit_test_pass_info
    file_cache_engine.update_test_pass_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST_SUCCESS,
    )
    # Test pass timestamp should be recorded
    relative_path = file_cache_engine._get_relative_path_to_subproject(
        file_in_subproject
    )
    assert relative_path in file_cache_engine.cache_data.unit_test_pass_info


def test_update_test_pass_timestamp_invalid_suite(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("The contents of a file!")
    with pytest.raises(
        ValueError, match="update_test_pass_timestamp only supports pass cache suites"
    ):
        file_cache_engine.update_test_pass_timestamp(
            file_path=file_in_subproject,
            cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
        )


def test_update_conftest_timestamp(
    file_cache_engine: FileCacheEngine, file_in_subproject: Path
) -> None:
    file_in_subproject.write_text("# conftest.py content")
    assert file_in_subproject not in file_cache_engine.cache_data.conftest_cache_info
    file_cache_engine.update_file_timestamp(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
    )
    assert not file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=file_in_subproject,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
    )


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
    test_root_dir = mock_subproject.get_test_dir()
    top_test_conftest = test_root_dir.joinpath("conftest.py")
    top_test_conftest.parent.mkdir(parents=True)
    top_test_conftest.touch()
    file_cache_engine.update_file_timestamp(
        file_path=top_test_conftest,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.UNIT_TEST,
    )
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
                    conftest = test_folder.joinpath("conftest.py")
                    conftest.touch()
                    if test_folder.name == "a":
                        file_cache_engine.update_file_timestamp(
                            file_path=conftest,
                            cache_info_suite=FileCacheEngine.CacheInfoSuite.CONFTEST,
                        )
                test_folder_added.add(test_folder)
            test_folder.joinpath(f"test_{src_file.name}").touch()
    expected_unit_test_info = [
        # Root level files
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("file1.py"),
            test_file_path=unit_test_root_dir.joinpath("test_file1.py"),
        ),
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("file2.py"),
            test_file_path=unit_test_root_dir.joinpath("test_file2.py"),
        ),
        # Files in 'a' directory
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "file3.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "test_file3.py"),
        ),
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "file4.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "test_file4.py"),
        ),
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "file5.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "test_file5.py"),
        ),
        # Files in 'a/b' directory (conftest updated)
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "b", "file1.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "b", "test_file1.py"),
        ),
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "b", "file2.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "b", "test_file2.py"),
        ),
        # Files in 'a/c' directory
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "c", "file1.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "c", "test_file1.py"),
        ),
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "c", "file2.py"),
            test_file_path=unit_test_root_dir.joinpath("a", "c", "test_file2.py"),
        ),
        # File in 'a/d/e' directory (conftest updated)
        UnitTestInfo(
            src_file_path=python_pkg_root_dir.joinpath("a", "d", "e", "some_file.py"),
            test_file_path=unit_test_root_dir.joinpath(
                "a", "d", "e", "test_some_file.py"
            ),
        ),
    ]
    assert list(file_cache_engine.get_unit_tests_to_run()) == expected_unit_test_info


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


@pytest.mark.usefixtures("mock_local_pyproject_toml_file")
def test_get_feature_test_info(
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
    test_root_dir = mock_subproject.get_test_dir()
    top_test_conftest = test_root_dir.joinpath("conftest.py")
    top_test_conftest.parent.mkdir(parents=True)
    top_test_conftest.touch()
    file_cache_engine._file_has_been_changed_since_last_timestamp_update(
        file_path=top_test_conftest,
        cache_info_suite=FileCacheEngine.CacheInfoSuite.FEATURE_TEST,
    )
    feature_test_root_dir = mock_subproject.get_test_suite_dir(
        test_suite=PythonSubproject.TestSuite.FEATURE_TESTS
    )
    feature_test_conftest = feature_test_root_dir.joinpath("conftest.py")
    feature_test_conftest.parent.mkdir(parents=True)
    feature_test_conftest.touch()
    feature_test_root_dir.joinpath("__init__.py").touch()
    feature_test_1 = feature_test_root_dir.joinpath("test_TICKET001_project_name.py")
    feature_test_1.touch()
    feature_test_2 = feature_test_root_dir.joinpath("test_TICKET002_project_name.py")
    feature_test_2.touch()
    py_file_in_test_folder = feature_test_root_dir.joinpath("other.py")
    py_file_in_test_folder.touch()
    other_file_in_test_folder = feature_test_root_dir.joinpath("other.txt")
    other_file_in_test_folder.touch()
    src_files_to_record = []
    for relative_src_file_to_create in sorted(relative_src_files_to_create):
        src_file = python_pkg_root_dir.joinpath(*relative_src_file_to_create)
        src_folder = src_file.parent
        src_folder.mkdir(parents=True, exist_ok=True)
        src_file.touch()
        if src_file.name.endswith(".py") and src_file.name not in "__init__.py":
            src_files_to_record.append(src_file)
    expected_feature_test_info = FeatureTestInfo(
        conftest_or_parent_conftest_was_updated=ParentConftestStatus.UPDATED,
        src_files=sorted(src_files_to_record),
        test_files=[feature_test_1, feature_test_2],
    )
    assert file_cache_engine.get_feature_tests_to_run() == expected_feature_test_info
