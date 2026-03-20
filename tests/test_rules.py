from mergeradar.analysis.classifier import enrich_changed_files
from mergeradar.analysis.context_builder import build_context
from mergeradar.analysis.scorer import score_context
from mergeradar.models import ChangedFile


def test_risky_change_without_tests_is_medium_or_higher() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(path="app/auth/service.py", old_path=None, status="M", additions=20, deletions=4),
            ChangedFile(path="alembic/versions/123_add_users.py", old_path=None, status="A", additions=30, deletions=0),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.score >= 6
    assert report.risk_level == "High"
    assert any(rule.id == "evidence.no_tests_for_risky_change" for rule in report.triggered_rules)


def test_docs_only_change_reduces_risk() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(path="docs/setup.md", old_path=None, status="M", additions=12, deletions=1),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.risk_level == "Low"
