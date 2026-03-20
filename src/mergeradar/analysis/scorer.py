from __future__ import annotations

from mergeradar.analysis.recommendations import build_missing_evidence, build_recommendations
from mergeradar.models import AnalysisContext, RiskReport, TriggeredRule
from mergeradar.rules import get_rules


def calculate_risk_level(score: int) -> str:
    """Calculate the risk level based on the total score from triggered rules.

    Args:
        score (int): Total score from triggered rules.

    Returns:
        str: Risk level as "Low", "Medium", or "High".
    """

    if score >= 6:
        return "High"

    if score >= 3:
        return "Medium"

    return "Low"


def build_summary(context: AnalysisContext, triggered_rules: list[TriggeredRule]) -> str:
    """Build a summary of the analysis context and triggered rules.

    Args:
        context (AnalysisContext): The analysis context.
        triggered_rules (list[TriggeredRule]): List of triggered rules.

    Returns:
        str: Summary of the analysis.
    """

    categories = ", ".join(sorted(context.categories_touched)) or "unknown areas"
    if not triggered_rules:
        return f"This change touches {categories} with no risk signals triggered by the current rule set."

    strongest = sorted(triggered_rules, key=lambda rule: rule.score, reverse=True)[:3]
    focus = ", ".join(rule.title.lower() for rule in strongest)
    return f"This change touches {categories} and triggered the following main signals: {focus}."


def score_context(context: AnalysisContext) -> RiskReport:
    """Score the analysis context and return a risk report.

    Args:
        context (AnalysisContext): The analysis context.

    Returns:
        RiskReport: The risk report for the given context.
    """

    triggered_rules: list[TriggeredRule] = []
    for rule in get_rules():
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
