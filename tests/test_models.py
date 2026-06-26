from mergeradar.models import ChangedFile, RiskReport, TriggeredRule


def test_changed_file_to_dict() -> None:
    cf = ChangedFile(
        path="app/auth.py",
        old_path="app/old_auth.py",
        status="R",
        additions=5,
        deletions=2,
        category="auth",
        classification_reason="auth keyword",
        top_level_component="app",
    )
    d = cf.to_dict()
    assert d["path"] == "app/auth.py"
    assert d["old_path"] == "app/old_auth.py"
    assert d["status"] == "R"
    assert d["additions"] == 5
    assert d["deletions"] == 2
    assert d["category"] == "auth"
    assert d["classification_reason"] == "auth keyword"
    assert d["top_level_component"] == "app"


def test_changed_file_to_dict_defaults() -> None:
    cf = ChangedFile(path="readme.md", old_path=None, status="M", additions=1, deletions=0)
    d = cf.to_dict()
    assert d["category"] == "unknown"
    assert d["classification_reason"] is None
    assert d["top_level_component"] is None


def test_triggered_rule_to_dict() -> None:
    rule = TriggeredRule(
        id="auth.path_touched",
        title="Auth-sensitive code changed",
        score=3,
        reason="app/auth.py",
        paths=["app/auth.py"],
    )
    d = rule.to_dict()
    assert d["id"] == "auth.path_touched"
    assert d["title"] == "Auth-sensitive code changed"
    assert d["score"] == 3
    assert d["reason"] == "app/auth.py"
    assert d["paths"] == ["app/auth.py"]


def test_risk_report_to_dict() -> None:
    cf = ChangedFile(path="main.py", old_path=None, status="M", additions=2, deletions=1)
    rule = TriggeredRule(id="scope.large_diff", title="Large diff", score=1, reason="big change")
    report = RiskReport(
        risk_level="Medium",
        score=4,
        summary="Medium risk.",
        triggered_rules=[rule],
        missing_evidence=["No tests."],
        recommendations=["Add tests."],
        changed_files=[cf],
        metadata={"total_files_changed": 1},
    )
    d = report.to_dict()
    assert d["risk_level"] == "Medium"
    assert d["score"] == 4
    assert d["summary"] == "Medium risk."
    assert len(d["triggered_rules"]) == 1
    assert d["triggered_rules"][0]["id"] == "scope.large_diff"
    assert d["missing_evidence"] == ["No tests."]
    assert d["recommendations"] == ["Add tests."]
    assert len(d["changed_files"]) == 1
    assert d["changed_files"][0]["path"] == "main.py"
    assert d["metadata"]["total_files_changed"] == 1
