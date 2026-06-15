from __future__ import annotations

from pathlib import Path


def is_git_repo(repo_path: Path) -> bool:
    """Return whether a path contains a Git metadata entry."""

    return (repo_path / ".git").exists()
