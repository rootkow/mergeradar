from __future__ import annotations

from mergeradar.analysis.context_builder import has_risky_changes
from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class NoTestsForRiskyChangeRule(SimpleRule):
    """Detect risky changes that do not include test changes."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result for risky changes without accompanying tests."""

        if not has_risky_changes(context) or context.has_test_changes:
            return None

        return self.trigger("Risky categories changed but no test file changes were detected.")


class NoDocsForRiskyChangeRule(SimpleRule):
    """Detect risky changes that do not include documentation changes."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result for risky changes without accompanying documentation."""

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
