from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from mergeradar.models import AnalysisContext, TriggeredRule


class Rule(Protocol):
    """Interface implemented by analysis rules.

    Attributes:
        id: Unique dotted identifier (e.g. "db.migration_changed").
        title: Human-readable rule name.
        score: Risk contribution when triggered (positive = risk, negative = stabilizer).
    """

    id: str
    title: str
    score: int

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a triggered result when the context matches this rule."""


@dataclass(slots=True)
class SimpleRule(ABC):
    """Abstract base rule containing shared result metadata.

    Subclasses must implement ``evaluate``.
    """

    id: str
    title: str
    score: int

    @abstractmethod
    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        ...

    def trigger(self, reason: str, paths: list[str] | None = None) -> TriggeredRule:
        """Create a triggered result with the rule's metadata and a reason."""

        return TriggeredRule(
            id=self.id,
            title=self.title,
            score=self.score,
            reason=reason,
            paths=paths or [],
        )


@dataclass(slots=True)
class CategoryChangedRule(SimpleRule):
    """Rule that matches changed files assigned to a specific category."""

    category: str
    reason_prefix: str

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Return a result when the context contains the configured category."""

        paths = [
            changed_file.path
            for changed_file in context.changed_files
            if changed_file.category == self.category
        ]
        if not paths:
            return None

        shown_paths = paths[:3]
        return self.trigger(f"{self.reason_prefix}: {', '.join(shown_paths)}", paths=shown_paths)
