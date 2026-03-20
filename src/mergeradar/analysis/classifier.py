from __future__ import annotations

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


def classify_file(path: str) -> str:
    """Classify a file based on its path and name.

    Args:
        path (str): The file path to classify.

    Returns:
        str: The category of the file.
    """

    parts = normalized_parts(path)
    filename = PurePosixPath(path).name
    suffix = PurePosixPath(path).suffix.lower()
    joined = "/".join(parts)

    if any(keyword in joined for keyword in MIGRATION_KEYWORDS):
        return "database"

    if "docs" in parts or suffix in DOC_EXTENSIONS or filename.lower() == "readme.md":
        return "docs"

    if any(keyword in parts or keyword in filename.lower() for keyword in TEST_KEYWORDS):
        return "tests"

    if filename in INFRA_FILENAMES or any(keyword in joined for keyword in INFRA_KEYWORDS):
        return "infra"

    if suffix in CONFIG_EXTENSIONS or any(keyword in joined for keyword in {"config", "settings", "values"}):
        return "config"

    if suffix in CODE_EXTENSIONS:
        if any(keyword in joined for keyword in AUTH_KEYWORDS):
            return "auth"

        if any(keyword in joined for keyword in API_KEYWORDS):
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
