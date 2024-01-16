from dataclasses import dataclass
from pathlib import Path

from dataclasses_json import dataclass_json

PROJECT_ROOT_DIR: Path

def project_root_dir() -> Path: ...
def project_build_dir(project_root_dir: Path) -> Path: ...
def git_info_file(project_build_dir: Path) -> Path: ...
@dataclass_json
@dataclass
class GitInfo:
    branch: str
    tags: list[str]
    def __init__(self, branch) -> None: ...

def git_info(git_info_file: Path) -> GitInfo: ...
def is_on_main(git_info: GitInfo): ...
