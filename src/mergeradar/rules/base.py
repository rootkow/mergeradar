from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mergeradar.models import AnalysisContext, TriggeredRule


class Rule(Protocol):
    """Protocol for a rule that can be evaluated against an analysis context."""

    id: str
    title: str
    score: int

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None: ...


@dataclass(slots=True)
class SimpleRule:
    """A simple rule that can be triggered with a reason."""

    id: str
    title: str
    score: int

    def trigger(self, reason: str) -> TriggeredRule:
        """Trigger the rule with the given reason.

        Args:
            reason: The reason for triggering the rule.

        Returns:
            A TriggeredRule object representing the triggered rule.
        """

        return TriggeredRule(id=self.id, title=self.title, score=self.score, reason=reason)
