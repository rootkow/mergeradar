import json

from mergeradar.models import RiskReport, TriggeredRule
from mergeradar.renderers.sarif import SARIF_SCHEMA, render_sarif


def test_sarif_includes_schema_and_version() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="No issues.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    assert doc["$schema"] == SARIF_SCHEMA
    assert doc["version"] == "2.1.0"


def test_sarif_includes_tool_info() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="No issues.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    driver = doc["runs"][0]["tool"]["driver"]
    assert driver["name"] == "MergeRadar"
    assert driver["version"] == "0.1.0"
    assert "informationUri" in driver


def test_sarif_includes_properties() -> None:
    report = RiskReport(
        risk_level="High",
        score=8,
        summary="Risky.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    props = doc["runs"][0]["properties"]
    assert props["riskScore"] == 8
    assert props["riskLevel"] == "High"


def test_sarif_triggered_rule_becomes_result() -> None:
    report = RiskReport(
        risk_level="Medium",
        score=3,
        summary="Auth change.",
        triggered_rules=[
            TriggeredRule(
                id="auth.path_touched",
                title="Auth-sensitive code changed",
                score=3,
                reason="Detected auth-sensitive code changes in: app/auth.py",
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    results = doc["runs"][0]["results"]
    assert len(results) == 1
    assert results[0]["ruleId"] == "auth.path_touched"
    assert results[0]["level"] == "warning"
    assert "app/auth.py" in results[0]["message"]["text"]


def test_sarif_positive_score_is_warning() -> None:
    report = RiskReport(
        risk_level="Low",
        score=1,
        summary="Minor.",
        triggered_rules=[
            TriggeredRule(id="test.rule", title="Test", score=1, reason="Something minor."),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    assert doc["runs"][0]["results"][0]["level"] == "warning"


def test_sarif_negative_score_is_note() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Stabilizer applied.",
        triggered_rules=[
            TriggeredRule(
                id="stability.docs_only",
                title="Docs-only change",
                score=-2,
                reason="Only documentation files changed.",
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    assert doc["runs"][0]["results"][0]["level"] == "note"


def test_sarif_result_includes_locations_from_reason() -> None:
    report = RiskReport(
        risk_level="Medium",
        score=5,
        summary="Multi-file change.",
        triggered_rules=[
            TriggeredRule(
                id="infra.config_changed",
                title="Infrastructure changed",
                score=2,
                reason=(
                    "Detected deployment or infrastructure changes in: "
                    "deploy/main.tf, Dockerfile"
                ),
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    result = doc["runs"][0]["results"][0]
    uris = [loc["physicalLocation"]["artifactLocation"]["uri"] for loc in result["locations"]]
    assert uris == ["deploy/main.tf", "Dockerfile"]


def test_sarif_no_locations_when_no_paths_in_reason() -> None:
    report = RiskReport(
        risk_level="Medium",
        score=2,
        summary="No tests.",
        triggered_rules=[
            TriggeredRule(
                id="evidence.no_tests_for_risky_change",
                title="No tests changed for risky areas",
                score=2,
                reason="Risky categories changed but no test file changes were detected.",
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    result = doc["runs"][0]["results"][0]
    assert "locations" not in result


def test_sarif_empty_results_when_no_rules_triggered() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Clean.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    assert doc["runs"][0]["results"] == []


def test_sarif_includes_column_kind() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary=".",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    doc = json.loads(render_sarif(report))
    assert doc["runs"][0]["columnKind"] == "unicodeCodePoints"
