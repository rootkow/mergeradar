from mergeradar.analysis.scorer import build_summary, calculate_risk_level
from mergeradar.models import AnalysisContext, TriggeredRule


def test_calculate_risk_level_low() -> None:
    assert calculate_risk_level(0) == "Low"
    assert calculate_risk_level(1) == "Low"
    assert calculate_risk_level(2) == "Low"


def test_calculate_risk_level_medium() -> None:
    assert calculate_risk_level(3) == "Medium"
    assert calculate_risk_level(4) == "Medium"
    assert calculate_risk_level(5) == "Medium"


def test_calculate_risk_level_high() -> None:
    assert calculate_risk_level(6) == "High"
    assert calculate_risk_level(10) == "High"
    assert calculate_risk_level(100) == "High"


def test_build_summary_with_no_rules() -> None:
    context = AnalysisContext(
        repo_path=".",
        changed_files=[],
        categories_touched={"docs"},
        components_touched=set(),
        has_test_changes=False,
        has_doc_changes=True,
        has_migration_changes=False,
        has_infra_changes=False,
        has_config_changes=False,
        has_auth_changes=False,
        has_api_changes=False,
        has_dep_changes=False,
        total_files_changed=0,
        total_additions=0,
        total_deletions=0,
    )
    summary = build_summary(context, [])
    assert "docs" in summary
    assert "no risk signals" in summary


def test_build_summary_with_rules() -> None:
    context = AnalysisContext(
        repo_path=".",
        changed_files=[],
        categories_touched={"auth", "database"},
        components_touched=set(),
        has_test_changes=False,
        has_doc_changes=False,
        has_migration_changes=True,
        has_infra_changes=False,
        has_config_changes=False,
        has_auth_changes=True,
        has_api_changes=False,
        has_dep_changes=False,
        total_files_changed=2,
        total_additions=10,
        total_deletions=2,
    )
    rules = [
        TriggeredRule(
            id="auth.path_touched",
            title="Auth-sensitive code changed",
            score=3,
            reason="app/auth.py",
        ),
        TriggeredRule(
            id="db.migration_changed",
            title="Database migration changed",
            score=3,
            reason="alembic/001.py",
        ),
    ]
    summary = build_summary(context, rules)
    assert "auth" in summary
    assert "database" in summary
    assert "auth-sensitive" in summary or "database migration" in summary


def test_build_summary_empty_categories() -> None:
    context = AnalysisContext(
        repo_path=".",
        changed_files=[],
        categories_touched=set(),
        components_touched=set(),
        has_test_changes=False,
        has_doc_changes=False,
        has_migration_changes=False,
        has_infra_changes=False,
        has_config_changes=False,
        has_auth_changes=False,
        has_api_changes=False,
        has_dep_changes=False,
        total_files_changed=0,
        total_additions=0,
        total_deletions=0,
    )
    summary = build_summary(context, [])
    assert "unknown areas" in summary
