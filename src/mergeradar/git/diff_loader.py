from __future__ import annotations

import re
import subprocess
from pathlib import Path

from mergeradar.models import ChangedFile

DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")
HUNK_RE = re.compile(r"^@@ .+ @@")


class DiffLoaderError(RuntimeError):
    """Custom error for issues encountered while loading git diffs."""

    pass


def load_changed_files(repo_path: Path, base: str | None = None, head: str | None = None) -> list[ChangedFile]:
    """Load changed files from a git repository diff.

    Args:
        repo_path (Path): Path to the local git repository.
        base (str | None): Base ref to diff from. Defaults to None.
        head (str | None): Head ref to diff to. Defaults to None.

    Raises:
        DiffLoaderError: If the git diff command fails or if no file changes are found.

    Returns:
        list[ChangedFile]: List of ChangedFile objects representing the changes.
    """

    spec = _build_spec(base=base, head=head)
    name_status_output = _run_git_diff(repo_path, ["--find-renames", "--name-status", spec])
    numstat_output = _run_git_diff(repo_path, ["--find-renames", "--numstat", spec])
    return _merge_name_status_and_numstat(name_status_output, numstat_output)


def load_changed_files_from_diff_file(diff_file: Path) -> list[ChangedFile]:
    """Parse a unified diff file and return a list of ChangedFile objects.

    Args:
        diff_file (Path): Path to the unified diff file.

    Raises:
        DiffLoaderError: If no file changes are found.

    Returns:
        list[ChangedFile]: List of ChangedFile objects representing the changes.
    """

    content = diff_file.read_text(encoding="utf-8")
    files: list[ChangedFile] = []
    current_path: str | None = None
    old_path: str | None = None
    additions = 0
    deletions = 0

    for raw_line in content.splitlines():
        header_match = DIFF_HEADER_RE.match(raw_line)
        if header_match:
            if current_path is not None:
                files.append(
                    ChangedFile(
                        path=current_path,
                        old_path=old_path,
                        status="M",
                        additions=additions,
                        deletions=deletions,
                    )
                )

            old_path = header_match.group(1)
            current_path = header_match.group(2)
            additions = 0
            deletions = 0
            continue

        if current_path is None or raw_line.startswith(("+++", "---")) or HUNK_RE.match(raw_line):
            continue

        if raw_line.startswith("+"):
            additions += 1
        elif raw_line.startswith("-"):
            deletions += 1

    if current_path is not None:
        files.append(
            ChangedFile(
                path=current_path,
                old_path=old_path,
                status="M",
                additions=additions,
                deletions=deletions,
            )
        )

    if not files:
        raise DiffLoaderError(f"No parseable file changes found in diff file: {diff_file}")

    return files


def _build_spec(base: str | None, head: str | None) -> str:
    """Build the git diff spec string based on the provided base and head refs."""

    if base and head:
        return f"{base}...{head}"

    if base and not head:
        return f"{base}...HEAD"

    return "HEAD"


def _run_git_diff(repo_path: Path, args: list[str]) -> str:
    """Run a git diff command in the specified repository and return the output."""

    command = ["git", "-C", str(repo_path), "diff", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git diff error"
        raise DiffLoaderError(stderr)

    return result.stdout


def _merge_name_status_and_numstat(name_status_output: str, numstat_output: str) -> list[ChangedFile]:
    """Merge the output of git diff --name-status and git diff --numstat into a list of ChangedFile objects."""

    numstat_map: dict[str, tuple[int, int]] = {}
    for line in numstat_output.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < 3:
            continue

        additions_raw, deletions_raw, path = parts[0], parts[1], parts[-1]
        additions = int(additions_raw) if additions_raw.isdigit() else 0
        deletions = int(deletions_raw) if deletions_raw.isdigit() else 0
        numstat_map[path] = (additions, deletions)

    changed_files: list[ChangedFile] = []
    for line in name_status_output.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        status = parts[0]
        old_path: str | None = None
        path = ""
        if status.startswith("R") and len(parts) >= 3:
            old_path, path = parts[1], parts[2]
            status = "R"
        elif len(parts) >= 2:
            path = parts[1]
        else:
            continue

        additions, deletions = numstat_map.get(path, (0, 0))

        changed_files.append(
            ChangedFile(
                path=path,
                old_path=old_path,
                status=status,
                additions=additions,
                deletions=deletions,
            )
        )

    if not changed_files:
        raise DiffLoaderError("No file changes found. Is your diff empty?")

    return changed_files
