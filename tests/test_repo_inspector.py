import subprocess
from pathlib import Path

from mergeradar.git.repo_inspector import is_git_repo


def test_is_git_repo_returns_true_for_repo_root(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    assert is_git_repo(tmp_path) is True


def test_is_git_repo_returns_true_for_repo_subdirectory(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subdir = tmp_path / "src"
    subdir.mkdir()

    assert is_git_repo(subdir) is True


def test_is_git_repo_returns_false_when_no_dot_git(tmp_path: Path) -> None:
    assert is_git_repo(tmp_path) is False
