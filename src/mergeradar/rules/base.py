from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mergeradar.models import AnalysisContext, TriggeredRule


class Rule(Protocol):
    """Interface implemented by analysis rules."""

    id: str
    title: str
    score: int

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a triggered result when the context matches this rule."""


@dataclass(slots=True)
class SimpleRule:
    """Base rule containing shared result metadata."""

    id: str
    title: str
    score: int

    def trigger(self, reason: str) -> TriggeredRule:
        """Create a triggered result with the rule's metadata and a reason."""

        return TriggeredRule(id=self.id, title=self.title, score=self.score, reason=reason)


@dataclass(slots=True)
class CategoryChangedRule(SimpleRule):
    """Rule that matches changed files assigned to a specific category."""

    category: str
    reason_prefix: str

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result when the context contains the configured category."""

        paths = [changed_file.path for changed_file in context.changed_files if changed_file.category == self.category]
        if not paths:
            return None

        return self.trigger(f"{self.reason_prefix}: {', '.join(paths[:3])}")
