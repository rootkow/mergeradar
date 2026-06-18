from __future__ import annotations

from mergeradar.models import TriggeredRule

RECOMMENDATIONS_BY_RULE = {
    "db.migration_changed": (
        "Validate the migration against a staging or snapshot dataset before deploy."
    ),
    "auth.path_touched": "Verify login, session, token refresh, and permission-protected flows.",
    "deps.changed": (
        "Review dependency diffs for known-vulnerability or breaking-change risk, "
        "and verify lockfile integrity."
    ),
    "infra.config_changed": (
        "Confirm deployment config and environment variables remain compatible."
    ),
    "api.surface_changed": (
        "Check backward compatibility for API consumers and regenerate any API docs if needed."
    ),
    "config.changed": "Review config defaults, secrets, and rollout safety across environments.",
    "evidence.no_tests_for_risky_change": (
        "Add or run targeted tests for the risky files changed in this diff."
    ),
    "evidence.no_docs_for_risky_change": (
        "Consider updating runbooks, README, or operational notes for behavior changes."
    ),
    "scope.large_diff": (
        "Break the change into smaller chunks or give reviewers a focused rollout plan."
    ),
    "scope.multiple_components_changed": (
        "Review blast radius across touched services or modules before merge."
    ),
}

MISSING_EVIDENCE_BY_RULE = {
    "evidence.no_tests_for_risky_change": "No tests were updated for risky changes.",
    "evidence.no_docs_for_risky_change": (
        "No documentation updates were detected for risky changes."
    ),
}


def build_recommendations(triggered_rules: list[TriggeredRule]) -> list[str]:
    """Return deduplicated recommendations for the triggered rules."""

    recommendations: list[str] = []
    for rule in triggered_rules:
        recommendation = RECOMMENDATIONS_BY_RULE.get(rule.id)
        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)

    if not recommendations:
        recommendations.append("No special checks were suggested based on the current rule set.")

    return recommendations


def build_missing_evidence(triggered_rules: list[TriggeredRule]) -> list[str]:
    """Return deduplicated evidence gaps for the triggered rules."""

    missing: list[str] = []
    for rule in triggered_rules:
        evidence = MISSING_EVIDENCE_BY_RULE.get(rule.id)
        if evidence and evidence not in missing:
            missing.append(evidence)

    return missing
