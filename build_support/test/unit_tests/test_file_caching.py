from pathlib import Path
from time import sleep
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from build_support.file_caching import FileCacheInfo


@pytest.fixture()
def file_checksum_data_dict() -> dict[str, Any]:
    return {
        "group_root_dir": "/usr/dev/tmp_path",
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


def test_load_bad_group_root_dir(file_checksum_data_dict: dict[str, Any]) -> None:
    file_checksum_data_dict["group_root_dir"] = 4
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


def test_check_on_new_file(tmp_path: Path) -> None:
    file_cache_info = FileCacheInfo(group_root_dir=tmp_path, cache_info={})
    new_file = tmp_path.joinpath("new_file")
    new_file.write_text("some contents")
    assert file_cache_info.file_has_been_changed(file_path=new_file)


def test_check_on_file_same(tmp_path: Path) -> None:
    file_cache_info = FileCacheInfo(group_root_dir=tmp_path, cache_info={})
    a_file = tmp_path.joinpath("a_file")
    a_file.write_text("The contents of a file!")
    assert file_cache_info.file_has_been_changed(file_path=a_file)
    assert not file_cache_info.file_has_been_changed(file_path=a_file)


def test_check_on_file_same_dump_and_read_cache(tmp_path: Path) -> None:
    file_cache_info = FileCacheInfo(group_root_dir=tmp_path, cache_info={})
    a_file = tmp_path.joinpath("path", "to", "a_file")
    a_file.parent.mkdir(parents=True)
    a_file.write_text("The contents of a file!")
    assert file_cache_info.file_has_been_changed(file_path=a_file)
    cache_file = tmp_path.joinpath("cache_file")
    cache_file.write_text(file_cache_info.to_yaml())
    new_file_cache_info = FileCacheInfo.from_yaml(cache_file.read_text())
    assert not new_file_cache_info.file_has_been_changed(file_path=a_file)


def test_check_on_file_different(tmp_path: Path) -> None:
    file_cache_info = FileCacheInfo(group_root_dir=tmp_path, cache_info={})
    a_file = tmp_path.joinpath("path", "to", "a_file")
    a_file.parent.mkdir(parents=True)
    a_file.write_text("The contents of a file!")
    assert file_cache_info.file_has_been_changed(file_path=a_file)
    sleep(0.01)
    a_file.write_text("A file now has new contents!!!! Very shocking.")
    assert file_cache_info.file_has_been_changed(file_path=a_file)


def test_check_on_file_different_dump_and_read_cache(tmp_path: Path) -> None:
    file_cache_info = FileCacheInfo(group_root_dir=tmp_path, cache_info={})
    a_file = tmp_path.joinpath("a_file")
    a_file.write_text("The contents of a file!")
    assert file_cache_info.file_has_been_changed(file_path=a_file)
    sleep(0.01)
    a_file.write_text("A file now has new contents!!!! Very shocking.")
    cache_file = tmp_path.joinpath("cache_file")
    cache_file.write_text(file_cache_info.to_yaml())
    new_file_cache_info = FileCacheInfo.from_yaml(cache_file.read_text())
    assert new_file_cache_info.file_has_been_changed(file_path=a_file)
