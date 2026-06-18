from pathlib import Path

from mergeradar.git.repo_inspector import is_git_repo


def test_is_git_repo_returns_true_when_dot_git_exists(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert is_git_repo(tmp_path) is True


def test_is_git_repo_returns_false_when_no_dot_git(tmp_path: Path) -> None:
    assert is_git_repo(tmp_path) is False
