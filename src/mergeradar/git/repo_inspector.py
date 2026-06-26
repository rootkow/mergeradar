from __future__ import annotations

import subprocess
from pathlib import Path


def is_git_repo(repo_path: Path) -> bool:
    """Return whether a path is inside a Git work tree."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0 and result.stdout.strip() == "true"
