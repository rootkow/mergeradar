from __future__ import annotations

from mergeradar.rules.base import CategoryChangedRule


class DepsChangedRule(CategoryChangedRule):
    """Match changes classified as dependency or package management files."""


RULE = DepsChangedRule(
    id="deps.changed",
    title="Dependencies changed",
    score=2,
    category="deps",
    reason_prefix="Detected dependency or package manifest changes in",
)
