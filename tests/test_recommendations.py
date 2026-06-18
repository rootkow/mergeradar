from mergeradar.analysis.recommendations import build_missing_evidence, build_recommendations
from mergeradar.models import TriggeredRule


def test_build_recommendations_returns_messages_for_known_rules() -> None:
    rules = [
        TriggeredRule(
            id="auth.path_touched",
            title="Auth-sensitive code changed",
            score=3,
            reason="app/auth.py",
        ),
    ]
    result = build_recommendations(rules)
    assert len(result) == 1
    assert "login" in result[0]


def test_build_recommendations_from_multiple_rules() -> None:
    rules = [
        TriggeredRule(
            id="db.migration_changed",
            title="Database migration changed",
            score=3,
            reason="alembic/001.py",
        ),
        TriggeredRule(
            id="deps.changed", title="Dependencies changed", score=2, reason="requirements.txt"
        ),
    ]
    result = build_recommendations(rules)
    assert len(result) == 2
    assert any("migration" in r for r in result)
    assert any("dependency" in r for r in result)


def test_build_recommendations_deduplicates() -> None:
    rules = [
        TriggeredRule(
            id="auth.path_touched", title="Auth-sensitive code changed", score=3, reason="a.py"
        ),
        TriggeredRule(
            id="auth.path_touched", title="Auth-sensitive code changed", score=3, reason="b.py"
        ),
    ]
    result = build_recommendations(rules)
    assert len(result) == 1


def test_build_recommendations_default_when_no_rules() -> None:
    result = build_recommendations([])
    assert result == ["No special checks were suggested based on the current rule set."]


def test_build_recommendations_default_when_only_unknown_rules() -> None:
    rules = [
        TriggeredRule(id="unknown.rule", title="Unknown", score=1, reason="something"),
    ]
    result = build_recommendations(rules)
    assert result == ["No special checks were suggested based on the current rule set."]


def test_build_missing_evidence_returns_evidence_gaps() -> None:
    rules = [
        TriggeredRule(
            id="evidence.no_tests_for_risky_change",
            title="No tests changed for risky areas",
            score=2,
            reason="risky",
        ),
    ]
    result = build_missing_evidence(rules)
    assert len(result) == 1
    assert "tests" in result[0]


def test_build_missing_evidence_deduplicates() -> None:
    rules = [
        TriggeredRule(
            id="evidence.no_tests_for_risky_change", title="No tests changed", score=2, reason="x"
        ),
        TriggeredRule(
            id="evidence.no_tests_for_risky_change", title="No tests changed", score=2, reason="y"
        ),
    ]
    result = build_missing_evidence(rules)
    assert len(result) == 1


def test_build_missing_evidence_empty_when_no_evidence_rules() -> None:
    rules = [
        TriggeredRule(id="auth.path_touched", title="Auth", score=3, reason="app/auth.py"),
    ]
    result = build_missing_evidence(rules)
    assert result == []
