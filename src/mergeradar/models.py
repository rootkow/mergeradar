from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ChangedFile:
    """A file reported by a Git diff."""

    path: str
    old_path: str | None
    status: str
    additions: int
    deletions: int
    category: str = "unknown"
    classification_reason: str | None = None
    top_level_component: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the changed file."""

        return asdict(self)


@dataclass(slots=True)
class AnalysisContext:
    """Aggregate metadata derived from a collection of changed files."""

    repo_path: str
    changed_files: list[ChangedFile]
    categories_touched: set[str]
    components_touched: set[str]
    has_test_changes: bool
    has_doc_changes: bool
    has_migration_changes: bool
    has_infra_changes: bool
    has_config_changes: bool
    has_auth_changes: bool
    has_api_changes: bool
    has_dep_changes: bool
    total_files_changed: int
    total_additions: int
    total_deletions: int
    risky_categories: set[str] = field(default_factory=set)


@dataclass(slots=True)
class TriggeredRule:
    """A rule evaluation that contributed to an analysis report."""

    id: str
    title: str
    score: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the triggered rule."""

        return asdict(self)


@dataclass(slots=True)
class RiskReport:
    """The scored risk assessment for a collection of changed files."""

    risk_level: str
    score: int
    summary: str
    triggered_rules: list[TriggeredRule]
    missing_evidence: list[str]
    recommendations: list[str]
    changed_files: list[ChangedFile]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation of the report."""

        return {
            "risk_level": self.risk_level,
            "score": self.score,
            "summary": self.summary,
            "triggered_rules": [rule.to_dict() for rule in self.triggered_rules],
            "missing_evidence": self.missing_evidence,
            "recommendations": self.recommendations,
            "changed_files": [changed_file.to_dict() for changed_file in self.changed_files],
            "metadata": self.metadata,
        }
