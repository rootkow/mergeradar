from __future__ import annotations

from mergeradar.rules.base import CategoryChangedRule


class MigrationChangedRule(CategoryChangedRule):
    """Match changes classified as database migrations or schema code."""


RULE = MigrationChangedRule(
    id="db.migration_changed",
    title="Database migration changed",
    score=3,
    category="database",
    reason_prefix="Detected database or migration changes in",
)
