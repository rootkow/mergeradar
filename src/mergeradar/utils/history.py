from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class HistoryEntry:
    score: int
    risk_level: str
    commit: str = ""
    timestamp: str = ""

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
    """Load score history from a JSON file.

    Returns an empty list if the file does not exist.
    Raises ValueError if the file exists but is not a valid history JSON file.
    """

    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"History file '{path}' is not valid JSON: {e}"
        ) from e

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON array in history file '{path}', got {type(data).__name__}"
        )

    entries: list[HistoryEntry] = []
    for i, entry in enumerate(data):
        try:
            entries.append(HistoryEntry.from_dict(entry))
        except (KeyError, TypeError) as e:
            raise ValueError(
                f"History file '{path}', entry {i} has invalid schema: missing key {e}"
            ) from e
    return entries


def append_history(path: Path, score: int, risk_level: str, commit: str = "") -> None:
    """Append a score entry to the history file and keep only the 20 most recent."""

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
    """Return whether the risk score is increasing, decreasing, stable, or first_scan."""

    if previous_score is None:
        return "first_scan"
    if current_score > previous_score:
        return "increasing"
    if current_score < previous_score:
        return "decreasing"
    return "stable"
