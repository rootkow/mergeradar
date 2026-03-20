from __future__ import annotations

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class AuthPathTouchedRule(SimpleRule):
    """Rule that triggers when auth-sensitive code changes are detected."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not context.has_auth_changes:
            return None

        auth_paths = [f.path for f in context.changed_files if f.category == "auth"]
        reason = f"Detected auth-sensitive code changes in: {', '.join(auth_paths[:3])}"
        return self.trigger(reason)


RULE = AuthPathTouchedRule(
    id="auth.path_touched",
    title="Auth-sensitive code changed",
    score=3,
)
