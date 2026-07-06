from __future__ import annotations

from mergeradar.config import DEFAULT_RISKY_CATEGORIES, MergeRadarConfig
from mergeradar.models import AnalysisContext, ChangedFile


def build_context(
    repo_path: str,
    changed_files: list[ChangedFile],
    config: MergeRadarConfig | None = None,
    allow_filesystem_analysis: bool = True,
) -> AnalysisContext:
    """Build aggregate analysis metadata from classified changed files."""

    categories_touched = {changed_file.category for changed_file in changed_files}
    components_touched = {
        changed_file.top_level_component
        for changed_file in changed_files
        if changed_file.top_level_component is not None
    }

    risky_categories = (
        config.risky_categories if config is not None else DEFAULT_RISKY_CATEGORIES
    )
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
        has_dep_changes="deps" in categories_touched,
        total_files_changed=len(changed_files),
        total_additions=sum(changed_file.additions for changed_file in changed_files),
        total_deletions=sum(changed_file.deletions for changed_file in changed_files),
        risky_categories=risky_categories,
        allow_filesystem_analysis=allow_filesystem_analysis,
    )


def has_risky_changes(context: AnalysisContext) -> bool:
    """Return whether the context contains any risk-sensitive category."""

    risky = context.risky_categories
    return any(category in risky for category in context.categories_touched)
