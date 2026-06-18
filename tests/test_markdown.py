from mergeradar.models import ChangedFile, RiskReport, TriggeredRule
from mergeradar.renderers.markdown import _group_changed_files, render_markdown


def test_render_markdown_includes_risk_level() -> None:
    report = RiskReport(
        risk_level="Low",
        score=1,
        summary="Low-risk change.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=["No special checks were suggested based on the current rule set."],
        changed_files=[],
    )
    output = render_markdown(report)
    assert "**Low** (score: 1)" in output
    assert "MergeRadar Report" in output


def test_render_markdown_includes_triggered_rules() -> None:
    report = RiskReport(
        risk_level="High",
        score=8,
        summary="Risky change.",
        triggered_rules=[
            TriggeredRule(
                id="auth.path_touched",
                title="Auth-sensitive code changed",
                score=3,
                reason="app/auth.py",
            ),
        ],
        missing_evidence=[],
        recommendations=["Verify login flows."],
        changed_files=[],
    )
    output = render_markdown(report)
    assert "[+3]" in output
    assert "Auth-sensitive code changed" in output
    assert "app/auth.py" in output


def test_render_markdown_shows_no_risk_signals_when_empty() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Nothing risky.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=["Nothing to do."],
        changed_files=[],
    )
    output = render_markdown(report)
    assert "No risk signals were triggered" in output


def test_render_markdown_includes_missing_evidence() -> None:
    report = RiskReport(
        risk_level="Medium",
        score=4,
        summary="Risky without tests.",
        triggered_rules=[
            TriggeredRule(
                id="evidence.no_tests_for_risky_change", title="No tests", score=2, reason="risky"
            ),
        ],
        missing_evidence=["No tests were updated for risky changes."],
        recommendations=["Add tests."],
        changed_files=[],
    )
    output = render_markdown(report)
    assert "No tests were updated" in output


def test_render_markdown_shows_no_evidence_gaps_when_empty() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Safe.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    output = render_markdown(report)
    assert "No obvious evidence gaps were detected" in output


def test_render_markdown_includes_changed_files_grouped_by_category() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Some changes.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[
            ChangedFile(
                path="app/auth.py",
                old_path=None,
                status="M",
                additions=5,
                deletions=2,
                category="auth",
            ),
            ChangedFile(
                path="docs/readme.md",
                old_path=None,
                status="A",
                additions=10,
                deletions=0,
                category="docs",
            ),
        ],
    )
    output = render_markdown(report)
    assert "### Authentication / Authorization" in output
    assert "### Documentation" in output
    assert "`app/auth.py`" in output
    assert "`docs/readme.md`" in output
    assert "M, +5/-2" in output
    assert "A, +10/-0" in output


def test_group_changed_files_groups_by_category() -> None:
    files = [
        ChangedFile(
            path="a.py", old_path=None, status="M", additions=1, deletions=1, category="app"
        ),
        ChangedFile(
            path="b.py", old_path=None, status="A", additions=2, deletions=0, category="auth"
        ),
        ChangedFile(
            path="c.py", old_path=None, status="D", additions=0, deletions=3, category="app"
        ),
    ]
    grouped = _group_changed_files(files)
    assert list(grouped.keys()) == ["app", "auth"]
    assert len(grouped["app"]) == 2
    assert len(grouped["auth"]) == 1
