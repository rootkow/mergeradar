from mergeradar.models import RiskReport, TriggeredRule
from mergeradar.renderers.annotations import render_annotations


def test_annotations_empty_when_no_rules() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Clean.",
        triggered_rules=[],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    result = render_annotations(report)
    assert result == ""


def test_annotation_format_with_path() -> None:
    report = RiskReport(
        risk_level="High",
        score=3,
        summary="Auth change.",
        triggered_rules=[
            TriggeredRule(
                id="auth.path_touched",
                title="Auth-sensitive code changed",
                score=3,
                reason="Detected auth-sensitive code changes in: app/auth/service.py",
                paths=["app/auth/service.py"],
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    result = render_annotations(report)
    assert "::warning file=app/auth/service.py,line=1," in result
    assert "title=MergeRadar (Auth-sensitive code changed)" in result
    assert "::Detected auth-sensitive code changes" in result


def test_annotation_uses_structured_paths_without_reason_parsing() -> None:
    report = RiskReport(
        risk_level="High",
        score=3,
        summary="Auth change.",
        triggered_rules=[
            TriggeredRule(
                id="auth.path_touched",
                title="Auth-sensitive code changed",
                score=3,
                reason="Structured signal.",
                paths=["app/auth/service.py"],
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )

    result = render_annotations(report)

    assert "::warning file=app/auth/service.py,line=1," in result
    assert "::Structured signal." in result


def test_annotation_format_without_path() -> None:
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
    result = render_annotations(report)
    assert "::warning" in result
    assert "title=MergeRadar (No tests changed for risky areas)" in result
    assert "file=" not in result


def test_annotation_level_negative_score_is_notice() -> None:
    report = RiskReport(
        risk_level="Low",
        score=0,
        summary="Docs only.",
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
    result = render_annotations(report)
    assert "::notice" in result
    assert "warning" not in result


def test_annotation_extracts_paths_with_extensions() -> None:
    report = RiskReport(
        risk_level="High",
        score=4,
        summary="Multi-file.",
        triggered_rules=[
            TriggeredRule(
                id="infra.config_changed",
                title="Infrastructure or deployment config changed",
                score=2,
                reason=(
                    "Detected deployment or infrastructure changes in: "
                    "deploy/main.tf, Dockerfile"
                ),
                paths=["deploy/main.tf", "Dockerfile"],
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    result = render_annotations(report)
    assert "::warning file=deploy/main.tf," in result
    assert "Dockerfile" in result


def test_annotation_multiple_rules() -> None:
    report = RiskReport(
        risk_level="High",
        score=5,
        summary="Multiple signals.",
        triggered_rules=[
            TriggeredRule(
                id="auth.path_touched",
                title="Auth-sensitive code changed",
                score=3,
                reason="Detected auth-sensitive code changes in: app/auth.py",
                paths=["app/auth.py"],
            ),
            TriggeredRule(
                id="deps.changed",
                title="Dependencies changed",
                score=2,
                reason="Detected dependency or package manifest changes in: requirements.txt",
                paths=["requirements.txt"],
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    result = render_annotations(report)
    assert result.count("::warning") == 2
    assert "app/auth.py" in result
    assert "requirements.txt" in result


def test_annotation_escapes_property_values() -> None:
    report = RiskReport(
        risk_level="High",
        score=3,
        summary="Special chars.",
        triggered_rules=[
            TriggeredRule(
                id="custom.special",
                title="Config: auth, api",
                score=3,
                reason="Detected risky change in: app/auth:api.py",
                paths=["app/auth:api.py"],
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )

    result = render_annotations(report)

    assert "file=app/auth%3Aapi.py" in result
    assert "title=MergeRadar (Config%3A auth%2C api)" in result


def test_annotations_do_not_infer_paths_from_reason_text() -> None:
    report = RiskReport(
        risk_level="Medium",
        score=2,
        summary="Multi-component.",
        triggered_rules=[
            TriggeredRule(
                id="scope.multiple_components_changed",
                title="Multiple top-level components changed",
                score=2,
                reason="Multiple top-level components changed: app, api, infra",
            ),
        ],
        missing_evidence=[],
        recommendations=[],
        changed_files=[],
    )
    result = render_annotations(report)
    assert "file=" not in result
