from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class HistoryEntry:
    def __init__(self, score: int, risk_level: str, commit: str, timestamp: str) -> None:
        self.score = score
        self.risk_level = risk_level
        self.commit = commit
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "risk_level": self.risk_level,
            "commit": self.commit,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        return cls(
            score=data["score"],
            risk_level=data["risk_level"],
            commit=data.get("commit", ""),
            timestamp=data.get("timestamp", ""),
        )


def load_history(path: Path) -> list[HistoryEntry]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [HistoryEntry.from_dict(entry) for entry in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return []


def append_history(path: Path, score: int, risk_level: str, commit: str = "") -> None:
    entries = load_history(path)
    entries.append(
        HistoryEntry(
            score=score,
            risk_level=risk_level,
            commit=commit,
            timestamp=datetime.now(UTC).isoformat(),
        )
    )

    # keep only the 20 most recent entries
    entries = entries[-20:]
    path.write_text(
        json.dumps([e.to_dict() for e in entries], indent=2), encoding="utf-8"
    )


def compute_trend(current_score: int, previous_score: int | None) -> str:
    if previous_score is None:
        return "first_scan"
    if current_score > previous_score:
        return "increasing"
    if current_score < previous_score:
        return "decreasing"
    return "stable"
