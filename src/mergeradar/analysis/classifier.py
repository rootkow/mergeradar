from __future__ import annotations

import re
from pathlib import PurePosixPath

from mergeradar.config import MergeRadarConfig
from mergeradar.models import ChangedFile
from mergeradar.utils.patterns import (
    CODE_EXTENSIONS,
    CONFIG_EXTENSIONS,
    DEP_FILENAMES,
    DOC_EXTENSIONS,
    INFRA_FILENAMES,
    build_keyword_map,
    normalized_parts,
    top_level_component,
)

TOKEN_RE = re.compile(r"[^a-z0-9]+")
NORMALIZED_INFRA_FILENAMES = {name.lower() for name in INFRA_FILENAMES}
NORMALIZED_DEP_FILENAMES = {name.lower() for name in DEP_FILENAMES}


def _matches_path_keyword(path: str, keywords: set[str]) -> bool:
    """Return whether a path contains a keyword segment or filename token."""

    parts = normalized_parts(path)
    filename = parts[-1] if parts else ""
    tokens = {token for token in TOKEN_RE.split(filename) if token}
    joined = "/".join(parts)

    for keyword in keywords:
        normalized_keyword = keyword.lower()
        if "/" in normalized_keyword:
            if joined == normalized_keyword or joined.startswith(f"{normalized_keyword}/"):
                return True
        elif "." in normalized_keyword:
            if filename == normalized_keyword:
                return True
        elif normalized_keyword in parts or normalized_keyword in tokens:
            return True

    return False


def classify_file(path: str, config: MergeRadarConfig | None = None) -> tuple[str, str]:
    """Return (category, reason) inferred from a file path."""

    keyword_map = build_keyword_map(config.keywords if config is not None else None)
    parts = normalized_parts(path)
    filename = parts[-1] if parts else ""
    suffix = PurePosixPath(filename).suffix.lower()
    if _matches_path_keyword(path, keyword_map["database"]):
        return ("database", "path contains migration-related keyword")

    if "docs" in parts or suffix in DOC_EXTENSIONS or filename.lower() == "readme.md":
        return ("docs", "documentation file matched by path or extension")

    if _matches_path_keyword(path, keyword_map["tests"]):
        return ("tests", "path contains test-related keyword")

    if filename in NORMALIZED_INFRA_FILENAMES or _matches_path_keyword(path, keyword_map["infra"]):
        return ("infra", "infrastructure or deployment file matched")

    if filename.lower() in NORMALIZED_DEP_FILENAMES or _matches_path_keyword(
        path, keyword_map["deps"]
    ):
        return ("deps", "dependency or package manifest file matched")

    if suffix in CONFIG_EXTENSIONS or _matches_path_keyword(path, keyword_map["config"]):
        return ("config", "configuration file matched by extension or keyword")

    if suffix in CODE_EXTENSIONS:
        if _matches_path_keyword(path, keyword_map["auth"]):
            return ("auth", "path contains auth-related keyword")

        if _matches_path_keyword(path, keyword_map["api"]):
            return ("api", "path contains API-related keyword")

        return ("app", "application source code file")

    return ("unknown", "unrecognized file type")


def enrich_changed_files(
    changed_files: list[ChangedFile], config: MergeRadarConfig | None = None
) -> list[ChangedFile]:
    """Add classification metadata to changed files in place.

    Args:
        changed_files: Files to classify and assign to top-level components.

    Returns:
        The same list instance after its entries have been updated.
    """

    for changed_file in changed_files:
        category, reason = classify_file(changed_file.path, config=config)
        changed_file.category = category
        changed_file.classification_reason = reason
        changed_file.top_level_component = top_level_component(changed_file.path)

    return changed_files
