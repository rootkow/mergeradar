from __future__ import annotations

import re
import subprocess
from pathlib import Path

from mergeradar.models import ChangedFile

DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")
HUNK_RE = re.compile(r"^@@ .+ @@")
BRACED_RENAME_RE = re.compile(r"^(.*)\{.* => (.*)\}(.*)$")


class DiffLoaderError(RuntimeError):
    """Raised when a Git diff cannot be loaded or contains no changes."""


def load_changed_files(
    repo_path: Path,
    base: str | None = None,
    head: str | None = None,
) -> list[ChangedFile]:
    """Load changed files by running Git against a local repository.

    Args:
        repo_path: Local Git repository to inspect.
        base: Optional base ref for a three-dot comparison.
        head: Optional head ref. Requires `base`; defaults to `HEAD`.

    Raises:
        DiffLoaderError: If the comparison is invalid, Git fails, or no changes exist.

    Returns:
        Changed files with statuses and line counts.
    """

    spec = _build_spec(base=base, head=head)
    name_status_output = _run_git_diff(repo_path, ["--find-renames", "--name-status", spec])
    numstat_output = _run_git_diff(repo_path, ["--find-renames", "--numstat", spec])
    return _merge_name_status_and_numstat(name_status_output, numstat_output)


def load_changed_files_from_diff_file(diff_file: Path) -> list[ChangedFile]:
    """Parse changed files from a saved unified diff.

    Args:
        diff_file: UTF-8 unified diff to parse.

    Raises:
        DiffLoaderError: If the diff contains no parseable file changes.

    Returns:
        Changed files with statuses and line counts.
    """

    content = diff_file.read_text(encoding="utf-8")
    files: list[ChangedFile] = []
    current_path: str | None = None
    old_path: str | None = None
    additions = 0
    deletions = 0
    status = "M"

    for raw_line in content.splitlines():
        header_match = DIFF_HEADER_RE.match(raw_line)
        if header_match:
            if current_path is not None:
                files.append(
                    _build_changed_file(current_path, old_path, status, additions, deletions)
                )

            old_path = header_match.group(1)
            current_path = header_match.group(2)
            additions = 0
            deletions = 0
            status = "M"
            continue

        if raw_line.startswith("new file mode "):
            status = "A"
            continue

        if raw_line.startswith("deleted file mode "):
            status = "D"
            continue

        if raw_line.startswith("rename from "):
            old_path = raw_line.removeprefix("rename from ")
            status = "R"
            continue

        if raw_line.startswith("rename to "):
            current_path = raw_line.removeprefix("rename to ")
            status = "R"
            continue

        if current_path is None or raw_line.startswith(("+++", "---")) or HUNK_RE.match(raw_line):
            continue

        if raw_line.startswith("+"):
            additions += 1
        elif raw_line.startswith("-"):
            deletions += 1

    if current_path is not None:
        files.append(_build_changed_file(current_path, old_path, status, additions, deletions))

    if not files:
        raise DiffLoaderError(f"No parseable file changes found in diff file: {diff_file}")

    return files


def _build_changed_file(
    path: str,
    old_path: str | None,
    status: str,
    additions: int,
    deletions: int,
) -> ChangedFile:
    """Create a changed-file record from parsed diff metadata."""

    return ChangedFile(
        path=path,
        old_path=old_path,
        status=status,
        additions=additions,
        deletions=deletions,
    )


def _build_spec(base: str | None, head: str | None) -> str:
    """Build the Git diff revision spec for the requested comparison."""

    if head and not base:
        raise DiffLoaderError("--head requires --base.")

    if base and head:
        return f"{base}...{head}"

    if base and not head:
        return f"{base}...HEAD"

    return "HEAD"


def _run_git_diff(repo_path: Path, args: list[str]) -> str:
    """Run `git diff` in a repository and return its standard output."""

    command = ["git", "-C", str(repo_path), "diff", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git diff error"
        raise DiffLoaderError(stderr)

    return result.stdout


def _merge_name_status_and_numstat(
    name_status_output: str,
    numstat_output: str,
) -> list[ChangedFile]:
    """Combine Git status and line-count output into changed-file records."""

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
        numstat_map[_rename_destination(path)] = (additions, deletions)

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


def _rename_destination(path: str) -> str:
    """Extract the destination from Git's compact rename notation."""

    braced_match = BRACED_RENAME_RE.match(path)
    if braced_match:
        prefix, destination, suffix = braced_match.groups()
        return f"{prefix}{destination}{suffix}"

    if " => " in path:
        return path.rsplit(" => ", maxsplit=1)[1]

    return path
