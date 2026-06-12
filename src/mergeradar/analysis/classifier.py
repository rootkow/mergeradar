from __future__ import annotations

import re
from pathlib import PurePosixPath

from mergeradar.models import ChangedFile
from mergeradar.utils.patterns import (
    API_KEYWORDS,
    AUTH_KEYWORDS,
    CODE_EXTENSIONS,
    CONFIG_EXTENSIONS,
    DOC_EXTENSIONS,
    INFRA_FILENAMES,
    INFRA_KEYWORDS,
    MIGRATION_KEYWORDS,
    TEST_KEYWORDS,
    normalized_parts,
    top_level_component,
)

TOKEN_RE = re.compile(r"[^a-z0-9]+")
NORMALIZED_INFRA_FILENAMES = {name.lower() for name in INFRA_FILENAMES}


def _matches_path_keyword(path: str, keywords: set[str]) -> bool:
    """Return whether a path contains an explicit keyword segment or filename token."""

    parts = normalized_parts(path)
    filename = parts[-1] if parts else ""
    tokens = {token for token in TOKEN_RE.split(filename) if token}
    joined = "/".join(parts)

    for keyword in keywords:
        normalized_keyword = keyword.lower()
        if "/" in normalized_keyword:
            if normalized_keyword in joined:
                return True
        elif "." in normalized_keyword:
            if filename == normalized_keyword:
                return True
        elif normalized_keyword in parts or normalized_keyword in tokens:
            return True

    return False


def classify_file(path: str) -> str:
    """Classify a file based on its path and name.

    Args:
        path (str): The file path to classify.

    Returns:
        str: The category of the file.
    """

    parts = normalized_parts(path)
    filename = parts[-1] if parts else ""
    suffix = PurePosixPath(filename).suffix.lower()
    if _matches_path_keyword(path, MIGRATION_KEYWORDS):
        return "database"

    if "docs" in parts or suffix in DOC_EXTENSIONS or filename.lower() == "readme.md":
        return "docs"

    if _matches_path_keyword(path, TEST_KEYWORDS):
        return "tests"

    if filename in NORMALIZED_INFRA_FILENAMES or _matches_path_keyword(
        path, INFRA_KEYWORDS
    ):
        return "infra"

    if suffix in CONFIG_EXTENSIONS or _matches_path_keyword(
        path, {"config", "settings", "values"}
    ):
        return "config"

    if suffix in CODE_EXTENSIONS:
        if _matches_path_keyword(path, AUTH_KEYWORDS):
            return "auth"

        if _matches_path_keyword(path, API_KEYWORDS):
            return "api"

        return "app"

    return "unknown"


def enrich_changed_files(changed_files: list[ChangedFile]) -> list[ChangedFile]:
    """Enrich a list of ChangedFile objects with additional metadata.

    Args:
        changed_files (list[ChangedFile]): The list of ChangedFile objects to enrich.

    Returns:
        list[ChangedFile]: The enriched list of ChangedFile objects.
    """

    enriched: list[ChangedFile] = []
    for changed_file in changed_files:
        changed_file.category = classify_file(changed_file.path)
        changed_file.top_level_component = top_level_component(changed_file.path)
        enriched.append(changed_file)

    return enriched
