from __future__ import annotations

from mergeradar.analysis.context_builder import has_risky_changes
from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class NoTestsForRiskyChangeRule(SimpleRule):
    """Rule that triggers when risky changes are made without corresponding test changes."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not has_risky_changes(context) or context.has_test_changes:
            return None

        return self.trigger("Risky categories changed but no test file changes were detected.")


class NoDocsForRiskyChangeRule(SimpleRule):
    """Rule that triggers when risky changes are made without corresponding documentation changes."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not has_risky_changes(context) or context.has_doc_changes:
            return None

        return self.trigger("Risky categories changed but no documentation updates were detected.")


RULES = [
    NoTestsForRiskyChangeRule(
        id="evidence.no_tests_for_risky_change",
        title="No tests changed for risky areas",
        score=2,
    ),
    NoDocsForRiskyChangeRule(
        id="evidence.no_docs_for_risky_change",
        title="No docs changed for risky areas",
        score=1,
    ),
]
