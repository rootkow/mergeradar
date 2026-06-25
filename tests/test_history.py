import json
from pathlib import Path

from mergeradar.utils.history import (
    HistoryEntry,
    append_history,
    compute_trend,
    load_history,
)


def test_history_entry_to_dict() -> None:
    entry = HistoryEntry(
        score=5, risk_level="Medium", commit="abc123", timestamp="2025-01-01T00:00:00"
    )
    data = entry.to_dict()
    assert data["score"] == 5
    assert data["risk_level"] == "Medium"
    assert data["commit"] == "abc123"
    assert data["timestamp"] == "2025-01-01T00:00:00"


def test_history_entry_from_dict() -> None:
    data = {
        "score": 3,
        "risk_level": "Medium",
        "commit": "def456",
        "timestamp": "2025-06-01T12:00:00",
    }
    entry = HistoryEntry.from_dict(data)
    assert entry.score == 3
    assert entry.risk_level == "Medium"
    assert entry.commit == "def456"
    assert entry.timestamp == "2025-06-01T12:00:00"


def test_history_entry_from_dict_missing_optional() -> None:
    data = {"score": 0, "risk_level": "Low"}
    entry = HistoryEntry.from_dict(data)
    assert entry.score == 0
    assert entry.commit == ""
    assert entry.timestamp == ""


def test_load_history_returns_empty_when_no_file(tmp_path: Path) -> None:
    entries = load_history(tmp_path / "missing.json")
    assert entries == []


def test_load_history_returns_empty_on_corrupt_json(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    f.write_text("not valid json")
    entries = load_history(f)
    assert entries == []


def test_load_history_returns_empty_on_wrong_type(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    f.write_text('{"score": 5}')
    entries = load_history(f)
    assert entries == []


def test_append_and_load_history(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    append_history(f, score=5, risk_level="Medium", commit="abc")
    entries = load_history(f)
    assert len(entries) == 1
    assert entries[0].score == 5
    assert entries[0].risk_level == "Medium"
    assert entries[0].commit == "abc"


def test_append_history_prunes_to_20(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    for i in range(25):
        append_history(f, score=i, risk_level="Low", commit=str(i))
    entries = load_history(f)
    assert len(entries) == 20
    assert entries[0].score == 5
    assert entries[-1].score == 24


def test_compute_trend_first_scan() -> None:
    assert compute_trend(5, None) == "first_scan"


def test_compute_trend_increasing() -> None:
    assert compute_trend(8, 5) == "increasing"


def test_compute_trend_decreasing() -> None:
    assert compute_trend(3, 5) == "decreasing"


def test_compute_trend_stable() -> None:
    assert compute_trend(5, 5) == "stable"


def test_append_history_adds_timestamp(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    append_history(f, score=3, risk_level="Medium")
    entries = load_history(f)
    assert entries[0].timestamp != ""


def test_history_file_is_valid_json(tmp_path: Path) -> None:
    f = tmp_path / "history.json"
    append_history(f, score=1, risk_level="Low")
    data = json.loads(f.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["score"] == 1
