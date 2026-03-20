from __future__ import annotations

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class LargeDiffRule(SimpleRule):
    """Rule that triggers when the change exceeds a certain size threshold."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        churn = context.total_additions + context.total_deletions
        if churn < 400 and context.total_files_changed < 15:
            return None

        return self.trigger(f"Large change detected ({context.total_files_changed} files, {churn} lines of churn).")


class MultipleComponentsRule(SimpleRule):
    """Rule that triggers when multiple top-level components are changed."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if len(context.components_touched) < 3:
            return None

        components = ", ".join(sorted(context.components_touched)[:5])
        return self.trigger(f"Multiple top-level components changed: {components}")


class DocsOnlyRule(SimpleRule):
    """Rule that triggers when only documentation files are changed."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if context.categories_touched != {"docs"}:
            return None

        return self.trigger("Only documentation files changed.")


class TestsOnlyRule(SimpleRule):
    """Rule that triggers when only test files are changed."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

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
