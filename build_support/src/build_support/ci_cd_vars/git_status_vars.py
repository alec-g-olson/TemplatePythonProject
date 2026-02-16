"""Collection of all functions and variable that report git information.

Attributes:
    | MAIN_BRANCH_NAME: The name of the main branch for this repo.
"""

from collections.abc import Iterable
from pathlib import Path

from git import Commit, DiffIndex, FetchInfo, Head, Repo
from git.cmd import execute_kwargs
from git.diff import Diff

from build_support.ci_cd_vars.project_structure import (
    get_dockerfile,
    get_poetry_lock_file,
)
from build_support.ci_cd_vars.subproject_structure import (
    SubprojectContext,
    get_python_subproject,
    get_sorted_subproject_contexts,
)


def get_git_repo(project_root: Path) -> Repo:
    """Gets a python representation of the project's git repo.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Repo: This project's git repo.
    """
    return Repo(project_root)


def get_git_head(project_root: Path) -> Head:
    """Gets the branch that is currently checked out.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Head: The active commit/branch of the git repo.
    """
    return get_git_repo(project_root=project_root).active_branch


def get_current_branch_name(project_root: Path) -> str:
    """Gets the branch that is currently checked out.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The name of the active commit/branch of the git repo.
    """
    return get_git_head(project_root=project_root).name


MAIN_BRANCH_NAME = "main"


def current_branch_is_main(project_root: Path) -> bool:
    """Determines if the branch currently checked out is main.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        bool: Is the current branch the main branch.
    """
    return get_current_branch_name(project_root=project_root) == MAIN_BRANCH_NAME


def monkeypatch_git_python_execute_kwargs() -> None:
    """Monkey patches some execute kwargs, so we can run git as a local user in docker.

    Returns:
        None
    """
    execute_kwargs.add("user")
    execute_kwargs.add("group")


def git_fetch(
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> Iterable[FetchInfo]:
    """Fetches from the remote repo.

    Args:
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        Iterable[FetchInfo]: The name of the active commit/branch of the git repo.
    """
    monkeypatch_git_python_execute_kwargs()
    return (
        get_git_repo(project_root=project_root)
        .remote()
        .fetch(user=local_uid, group=local_gid, env=local_user_env)
    )


def get_local_tags(project_root: Path) -> list[str]:
    """Gets the tags on your local git instance.

    To get up-to-date remote tags run `git fetch` before this function.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        list[str]: The list of all tags on the local version of your git repo.
    """
    return [tag.name for tag in get_git_repo(project_root=project_root).tags]


def git_add_all(project_root: Path) -> Head:
    """Adds all files te the current git index.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Head: The active commit/branch of the git repo.
    """
    repo = get_git_repo(project_root=project_root)
    repo.git.add(update=True)
    return repo.active_branch


def get_git_diff(project_root: Path) -> DiffIndex[Diff]:
    """Gets the result of `git diff`.  If not empty, there are unstaged changes.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        str: The results of running `git diff`.
    """
    return git_add_all(project_root=project_root).commit.diff()


def commit_changes_if_diff(
    commit_message: str,
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> None:
    """Commits changes to the active branch if there are any uncommitted changes.

    Args:
        commit_message (str): The message that will be put on the commit if the commit
            is successful.
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        None
    """
    current_diff = get_git_diff(project_root=project_root)
    if current_diff:
        if current_branch_is_main(project_root=project_root):
            msg = (
                f"Attempting to push tags with unstaged changes to {MAIN_BRANCH_NAME}."
            )
            raise RuntimeError(msg)
        repo = get_git_repo(project_root=project_root)
        git_add_all(project_root=project_root)
        repo.index.commit(commit_message)
        monkeypatch_git_python_execute_kwargs()
        repo.remote().push(user=local_uid, group=local_gid, env=local_user_env)


def tag_current_commit_and_push(
    tag: str,
    project_root: Path,
    local_uid: int = 0,
    local_gid: int = 0,
    local_user_env: dict[str, str] | None = None,
) -> None:
    """Tags the working commit with the supplied tag, and pushes to remote.

    Args:
        tag (str): The message that the working commit will be tagged with.
        project_root (Path): Path to this project's root.
        local_uid (int): The local user's users id, allows running git as local user
            from inside a docker container.
        local_gid (int): The local user's group id, allows running git as local user
            from inside a docker container.
        local_user_env (dict[str, str] | None): The environment variables to use
            when running git commands as the local user from inside a docker container.

    Returns:
        None
    """
    repo = get_git_repo(project_root=project_root)
    repo.create_tag(tag)
    monkeypatch_git_python_execute_kwargs()
    repo.remote().push(tag, user=local_uid, group=local_gid, env=local_user_env)


def get_most_recent_commit_on_main(repo: Repo) -> Commit:
    """Gets the most recent commit on the main branch.

    Args:
        repo (Repo): The git repository for this project.

    Returns:
        Commit: The most recent commit on the main branch.
    """
    return repo.refs[f"origin/{MAIN_BRANCH_NAME}"].commit


def get_modified_files_between_commits(
    project_root: Path, repo: Repo, old_commit: Commit, new_commit: Commit
) -> set[Path]:
    """Gets the set of files that were modified between two commits.

    Args:
        project_root (Path): Path to this project's root.
        repo (Repo): The git repository for this project.
        old_commit (Commit): The older commit.
        new_commit (Commit): The newer commit.

    Returns:
        Set[Path]: The set of files that were modified between the two commits.
    """
    diff_index = repo.git.diff(old_commit.hexsha, new_commit.hexsha, name_only=True)
    return {project_root.joinpath(file) for file in diff_index.split() if file}


def get_modified_files(project_root: Path) -> set[Path]:
    """Gets the set of files that were modified since the most recent commit on main.

    This includes uncommitted changes.

    Args:
        project_root (Path): Path to this project's root.

    Returns:
        Set[Path]: The set of files that were modified.
    """
    repo = get_git_repo(project_root=project_root)

    if current_branch_is_main(project_root=project_root):
        current_commit = repo.head.commit
        parent_commit = current_commit.parents[0]
        modified_files = get_modified_files_between_commits(
            project_root=project_root,
            repo=repo,
            old_commit=parent_commit,
            new_commit=current_commit,
        )
    else:
        # If we're not on main, compare the HEAD with the most recent commit on main
        head_commit = repo.head.commit
        main_commit = get_most_recent_commit_on_main(repo=repo)
        modified_files = get_modified_files_between_commits(
            project_root=project_root,
            repo=repo,
            old_commit=main_commit,
            new_commit=head_commit,
        )
        # Add uncommitted files
        diff_index = repo.git.diff(name_only=True)
        uncommitted_files = {
            project_root.joinpath(file) for file in diff_index.split() if file
        }
        modified_files = modified_files.union(uncommitted_files)

    return modified_files


def get_modified_subprojects(
    modified_files: Iterable[Path], project_root: Path
) -> list[SubprojectContext]:
    """Gets the list of subprojects that have modified files and should be tested.

    This function will return the list of subprojects that have had files changed
    relative to the "parent" commit.  If the current branch is "main", then the "parent"
    commit is the previous commit on main.  If the current branch is not main, then the
    "parent" commit is the most recent commit on main.

    Once we have a list of all files that have been changed we can easily get a list of
    the subprojects those files belong to.  This can be helpful in reducing the work
    required by our CI/CD pipelines because if a subproject is completely unmodified
    then we don't need to run any tests or formatting checks on it.

    Args:
        modified_files (Iterable[Path]): The collection of files that have been modified
            since the most recent commit on main.
        project_root (Path): Path to this project's root.

    Returns:
        list[SubprojectContext]: The list of subprojects that have been modified.
    """
    modified_subprojects = []
    for subproject_context in get_sorted_subproject_contexts():
        subproject_root = get_python_subproject(
            subproject_context=subproject_context, project_root=project_root
        ).get_root_dir()
        if any(file.is_relative_to(subproject_root) for file in modified_files):
            modified_subprojects.append(subproject_context)
    return modified_subprojects


def dockerfile_was_modified(modified_files: Iterable[Path], project_root: Path) -> bool:
    """Checks if the dockerfile was modified.

    If the dockerfile has been modified it implies that our environment is different,
    and we should cast a wide net when testing.

    Args:
        modified_files (Iterable[Path]): The collection of files that have been modified
            since the most recent commit on main.
        project_root (Path): The root of the project.

    Returns:
        bool: Has the dockerfile been modified since the last commit on main.
    """
    return get_dockerfile(project_root=project_root) in modified_files


def poetry_lock_file_was_modified(
    modified_files: Iterable[Path], project_root: Path
) -> bool:
    """Checks if the poetry lock file was modified.

    If the poetry lock file has been modified it implies that our environment is
    different, and we should cast a wide net when testing.

    Args:
        modified_files (Iterable[Path]): The collection of files that have been modified
            since the most recent commit on main.
        project_root (Path): The root of the project.

    Returns:
        bool: Has the poetry lock file been modified since the last commit on main.
    """
    return get_poetry_lock_file(project_root=project_root) in modified_files
