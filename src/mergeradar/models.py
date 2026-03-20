from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ChangedFile:
    """Represents a file that has changed in a git repository."""

    path: str
    old_path: str | None
    status: str
    additions: int
    deletions: int
    category: str = "unknown"
    top_level_component: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisContext:
    """Represents the context of an analysis, including changed files and touched categories/components."""

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
    total_files_changed: int
    total_additions: int
    total_deletions: int


@dataclass(slots=True)
class TriggeredRule:
    """Represents a rule that has been triggered during analysis."""

    id: str
    title: str
    score: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskReport:
    """Represents a risk report generated from an analysis."""

    risk_level: str
    score: int
    summary: str
    triggered_rules: list[TriggeredRule]
    missing_evidence: list[str]
    recommendations: list[str]
    changed_files: list[ChangedFile]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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


@dataclass(slots=True)
class AnalyzeOptions:
    """Represents the options for analyzing a git repository or diff file."""

    repo_path: Path
    base: str | None = None
    head: str | None = None
    diff_file: Path | None = None
    output: Path | None = None
    output_format: str = "markdown"
    verbose: bool = False
