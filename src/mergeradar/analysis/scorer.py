from __future__ import annotations

from mergeradar.analysis.recommendations import build_missing_evidence, build_recommendations
from mergeradar.config import MergeRadarConfig
from mergeradar.models import AnalysisContext, RiskReport, TriggeredRule
from mergeradar.rules import get_rules

SUMMARY_CATEGORY_LABELS = {
    "app": "application code",
    "auth": "authentication",
    "api": "API surface",
    "database": "database",
    "deps": "dependencies",
    "infra": "infrastructure",
    "config": "configuration",
    "tests": "tests",
    "docs": "documentation",
    "unknown": "other files",
}


def calculate_risk_level(score: int) -> str:
    """Map a numeric risk score to its display level."""

    if score >= 6:
        return "High"

    if score >= 3:
        return "Medium"

    return "Low"


def build_summary(context: AnalysisContext, triggered_rules: list[TriggeredRule]) -> str:
    """Summarize the changed scope without repeating detailed report sections."""

    categories = _format_summary_categories(context.categories_touched)
    file_count = context.total_files_changed
    file_label = "file" if file_count == 1 else "files"
    change_size = (
        f"{file_count} {file_label}, "
        f"+{context.total_additions}/-{context.total_deletions}"
    )

    if not triggered_rules:
        return (
            f"This change touches {categories}.\n"
            f"Change size: {change_size}\n"
            "No risk signals were triggered by the current rule set"
        )

    signal_count = len(triggered_rules)
    signal_label = "signal" if signal_count == 1 else "signals"
    return (
        f"This change touches {categories}.\n"
        f"Change size: {change_size}\n"
        f"{signal_count} risk {signal_label} triggered"
    )


def _format_summary_categories(categories: set[str]) -> str:
    """Format internal category IDs for human-readable summary prose."""

    labels = [SUMMARY_CATEGORY_LABELS.get(category, category) for category in sorted(categories)]
    return ", ".join(labels) or "unclassified files"


def score_context(context: AnalysisContext, config: MergeRadarConfig | None = None) -> RiskReport:
    """Evaluate all rules and build a complete risk report."""

    triggered_rules: list[TriggeredRule] = []
    for rule in get_rules(config):
        triggered = rule.evaluate(context)
        if triggered is not None:
            triggered_rules.append(triggered)

    score = max(0, sum(rule.score for rule in triggered_rules))
    risk_level = calculate_risk_level(score)
    summary = build_summary(context, triggered_rules)

    return RiskReport(
        risk_level=risk_level,
        score=score,
        summary=summary,
        triggered_rules=triggered_rules,
        missing_evidence=build_missing_evidence(triggered_rules),
        recommendations=build_recommendations(triggered_rules),
        changed_files=context.changed_files,
        metadata={
            "total_files_changed": context.total_files_changed,
            "total_additions": context.total_additions,
            "total_deletions": context.total_deletions,
            "categories_touched": sorted(context.categories_touched),
            "components_touched": sorted(context.components_touched),
        },
    )
