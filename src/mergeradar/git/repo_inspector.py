from __future__ import annotations

from pathlib import Path


def is_git_repo(repo_path: Path) -> bool:
    """Check if the given path is a git repository by looking for a .git directory.

    Args:
        repo_path (Path): Path to check for a git repository.

    Returns:
        bool: True if the path is a git repository, False otherwise.
    """

    return (repo_path / ".git").exists()
