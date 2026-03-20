from __future__ import annotations

from mergeradar.models import AnalysisContext, ChangedFile

# TODO: Configurationize this
RISKY_CATEGORIES = {"database", "auth", "infra", "config", "api"}


def build_context(repo_path: str, changed_files: list[ChangedFile]) -> AnalysisContext:
    """Build an analysis context from a list of changed files.

    Args:
        repo_path (str): The path to the repository.
        changed_files (list[ChangedFile]): The list of changed files.

    Returns:
        AnalysisContext: The analysis context for the given changed files.
    """

    categories_touched = {changed_file.category for changed_file in changed_files}
    components_touched = {
        changed_file.top_level_component
        for changed_file in changed_files
        if changed_file.top_level_component is not None
    }

    return AnalysisContext(
        repo_path=repo_path,
        changed_files=changed_files,
        categories_touched=categories_touched,
        components_touched=components_touched,
        has_test_changes="tests" in categories_touched,
        has_doc_changes="docs" in categories_touched,
        has_migration_changes="database" in categories_touched,
        has_infra_changes="infra" in categories_touched,
        has_config_changes="config" in categories_touched,
        has_auth_changes="auth" in categories_touched,
        has_api_changes="api" in categories_touched,
        total_files_changed=len(changed_files),
        total_additions=sum(changed_file.additions for changed_file in changed_files),
        total_deletions=sum(changed_file.deletions for changed_file in changed_files),
    )


def has_risky_changes(context: AnalysisContext) -> bool:
    """Check if the analysis context has any risky changes.

    Args:
        context (AnalysisContext): The analysis context to check.

    Returns:
        bool: True if there are risky changes, False otherwise.
    """

    return any(category in RISKY_CATEGORIES for category in context.categories_touched)
