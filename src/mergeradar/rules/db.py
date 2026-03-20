from __future__ import annotations

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class MigrationChangedRule(SimpleRule):
    """Rule that triggers when database migration changes are detected."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not context.has_migration_changes:
            return None

        migration_paths = [f.path for f in context.changed_files if f.category == "database"]
        reason = f"Detected database or migration changes in: {', '.join(migration_paths[:3])}"
        return self.trigger(reason)


RULE = MigrationChangedRule(
    id="db.migration_changed",
    title="Database migration changed",
    score=3,
)
