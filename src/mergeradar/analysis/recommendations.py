from __future__ import annotations

from mergeradar.models import TriggeredRule

# TODO:
# - Configurationize these mappings
# - Integrate with model
RECOMMENDATIONS_BY_RULE = {
    "db.migration_changed": "Validate the migration against a staging or snapshot dataset before deploy.",
    "auth.path_touched": "Verify login, session, token refresh, and permission-protected flows.",
    "infra.config_changed": "Confirm deployment config and environment variables remain compatible.",
    "api.surface_changed": "Check backward compatibility for API consumers and regenerate any API docs if needed.",
    "config.changed": "Review config defaults, secrets, and rollout safety across environments.",
    "evidence.no_tests_for_risky_change": "Add or run targeted tests for the risky files changed in this diff.",
    "evidence.no_docs_for_risky_change": "Consider updating runbooks, README, or operational notes for behavior changes.",
    "scope.large_diff": "Break the change into smaller chunks or give reviewers a focused rollout plan.",
    "scope.multiple_components_changed": "Review blast radius across touched services or modules before merge.",
}

MISSING_EVIDENCE_BY_RULE = {
    "evidence.no_tests_for_risky_change": "No tests were updated for risky changes.",
    "evidence.no_docs_for_risky_change": "No documentation updates were detected for risky changes.",
}


def build_recommendations(triggered_rules: list[TriggeredRule]) -> list[str]:
    """Build a list of recommendations based on triggered rules.

    Args:
        triggered_rules (list[TriggeredRule]): The list of triggered rules.

    Returns:
        list[str]: A list of recommendations.
    """

    recommendations: list[str] = []
    for rule in triggered_rules:
        recommendation = RECOMMENDATIONS_BY_RULE.get(rule.id)
        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)

    if not recommendations:
        recommendations.append("No special checks were suggested based on the current rule set.")

    return recommendations


def build_missing_evidence(triggered_rules: list[TriggeredRule]) -> list[str]:
    """Build a list of missing evidence based on triggered rules.

    Args:
        triggered_rules (list[TriggeredRule]): The list of triggered rules.

    Returns:
        list[str]: A list of missing evidence.
    """

    missing: list[str] = []
    for rule in triggered_rules:
        evidence = MISSING_EVIDENCE_BY_RULE.get(rule.id)
        if evidence and evidence not in missing:
            missing.append(evidence)

    return missing
