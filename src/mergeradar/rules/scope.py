from __future__ import annotations

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class LargeDiffRule(SimpleRule):
    """Detect changes that exceed the configured size thresholds."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result when file count or line churn is large."""

        churn = context.total_additions + context.total_deletions
        if churn < 400 and context.total_files_changed < 15:
            return None

        return self.trigger(f"Large change detected ({context.total_files_changed} files, {churn} lines of churn).")


class MultipleComponentsRule(SimpleRule):
    """Detect changes spanning multiple top-level components."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result when at least three components are touched."""

        if len(context.components_touched) < 3:
            return None

        components = ", ".join(sorted(context.components_touched)[:5])
        return self.trigger(f"Multiple top-level components changed: {components}")


class DocsOnlyRule(SimpleRule):
    """Detect changes containing only documentation files."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a stabilizing result for documentation-only changes."""

        if context.categories_touched != {"docs"}:
            return None

        return self.trigger("Only documentation files changed.")


class TestsOnlyRule(SimpleRule):
    """Detect changes containing only test files."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a stabilizing result for test-only changes."""

        if context.categories_touched != {"tests"}:
            return None

        return self.trigger("Only test files changed.")


RULES = [
    LargeDiffRule(
        id="scope.large_diff",
        title="Large diff size threshold exceeded",
        score=1,
    ),
    MultipleComponentsRule(
        id="scope.multiple_components_changed",
        title="Multiple top-level components changed",
        score=2,
    ),
    DocsOnlyRule(
        id="stability.docs_only",
        title="Docs-only change",
        score=-2,
    ),
    TestsOnlyRule(
        id="stability.tests_only",
        title="Tests-only change",
        score=-1,
    ),
]
