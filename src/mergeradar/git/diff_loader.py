from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from mergeradar.exceptions import DiffLoaderError
from mergeradar.models import ChangedFile

DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")
HUNK_RE = re.compile(r"^@@ .+ @@")


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
    name_status_output = _run_git_diff(
        repo_path, ["--find-renames", "--name-status", "-z", spec]
    )
    numstat_output = _run_git_diff(repo_path, ["--find-renames", "--numstat", "-z", spec])
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

    try:
        content = diff_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise DiffLoaderError(f"Could not read diff file '{diff_file}': {exc}") from exc

    if not any(line.startswith("diff --git ") for line in content.splitlines()):
        return _parse_plain_unified_diff(content, diff_file)

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

        if raw_line.startswith("--- /dev/null"):
            status = "A"
            continue

        if raw_line.startswith("+++ /dev/null"):
            status = "D"
            continue

        if raw_line.startswith("Binary files "):
            if additions == 0:
                additions = 1
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


def _parse_plain_unified_diff(content: str, diff_file: Path) -> list[ChangedFile]:
    """Parse a unified diff that does not contain Git ``diff --git`` headers."""

    files: list[ChangedFile] = []
    old_path: str | None = None
    current_path: str | None = None
    additions = 0
    deletions = 0
    status = "M"
    in_hunk = False

    for raw_line in content.splitlines():
        if raw_line.startswith("--- "):
            if current_path is not None:
                files.append(
                    _build_changed_file(current_path, old_path, status, additions, deletions)
                )
            raw_old_path = _unified_header_path(raw_line, "--- ")
            old_path = None if raw_old_path == "/dev/null" else raw_old_path
            current_path = old_path
            additions = 0
            deletions = 0
            status = "A" if old_path is None else "M"
            in_hunk = False
            continue

        if raw_line.startswith("+++ ") and (old_path is not None or status == "A"):
            raw_new_path = _unified_header_path(raw_line, "+++ ")
            if raw_new_path == "/dev/null":
                status = "D"
            else:
                current_path = raw_new_path
            continue

        if HUNK_RE.match(raw_line):
            in_hunk = True
            continue

        if not in_hunk:
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


def _unified_header_path(line: str, prefix: str) -> str:
    """Extract and normalize a path from a ``---`` or ``+++`` header."""

    path = line.removeprefix(prefix).split("\t", 1)[0]
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


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


def _run_git_diff(repo_path: Path, args: list[str]) -> bytes:
    """Run `git diff` in a repository and return its standard output."""

    command = ["git", "-C", str(repo_path), "diff", *args]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        stderr = os.fsdecode(result.stderr).strip() or "unknown git diff error"
        raise DiffLoaderError(stderr)

    return result.stdout


def _merge_name_status_and_numstat(
    name_status_output: bytes,
    numstat_output: bytes,
) -> list[ChangedFile]:
    """Combine Git status and line-count output into changed-file records."""

    numstat_map: dict[str, tuple[int, int]] = {}
    numstat_fields = numstat_output.split(b"\0")
    field_index = 0
    while field_index < len(numstat_fields):
        record = numstat_fields[field_index]
        field_index += 1
        if not record:
            continue

        parts = record.split(b"\t", maxsplit=2)
        if len(parts) != 3:
            continue

        additions_raw, deletions_raw, raw_path = parts
        if not raw_path:
            if field_index + 1 >= len(numstat_fields):
                continue
            field_index += 1  # Skip the rename source path.
            raw_path = numstat_fields[field_index]
            field_index += 1

        path = os.fsdecode(raw_path)
        additions = int(additions_raw) if additions_raw.isdigit() else 0
        deletions = int(deletions_raw) if deletions_raw.isdigit() else 0
        numstat_map[path] = (additions, deletions)

    changed_files: list[ChangedFile] = []
    name_status_fields = name_status_output.split(b"\0")
    field_index = 0
    while field_index < len(name_status_fields):
        raw_status = name_status_fields[field_index]
        field_index += 1
        if not raw_status:
            continue

        status = os.fsdecode(raw_status)
        old_path: str | None = None
        if status.startswith(("R", "C")):
            if field_index + 1 >= len(name_status_fields):
                continue
            old_path = os.fsdecode(name_status_fields[field_index])
            path = os.fsdecode(name_status_fields[field_index + 1])
            field_index += 2
            status = status[0]
        elif field_index < len(name_status_fields):
            path = os.fsdecode(name_status_fields[field_index])
            field_index += 1
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
