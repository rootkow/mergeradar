from mergeradar.analysis.classifier import classify_file, enrich_changed_files
from mergeradar.analysis.context_builder import build_context
from mergeradar.analysis.scorer import score_context
from mergeradar.config import CustomRuleDef, MergeRadarConfig, RuleOverride
from mergeradar.models import ChangedFile
from mergeradar.rules import get_rules


def test_risky_change_without_tests_is_medium_or_higher() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="app/auth/service.py",
                old_path=None,
                status="M",
                additions=20,
                deletions=4,
            ),
            ChangedFile(
                path="alembic/versions/123_add_users.py",
                old_path=None,
                status="A",
                additions=30,
                deletions=0,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.score >= 6
    assert report.risk_level == "High"
    assert any(rule.id == "evidence.no_tests_for_risky_change" for rule in report.triggered_rules)


def test_dep_change_triggers_deps_rule() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="requirements.txt",
                old_path=None,
                status="M",
                additions=3,
                deletions=1,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.score >= 2
    assert any(rule.id == "deps.changed" for rule in report.triggered_rules)


def test_lockfile_only_reduces_risk() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="package-lock.json",
                old_path=None,
                status="M",
                additions=40,
                deletions=10,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.risk_level == "Low"
    assert any(rule.id == "stability.lockfile_only" for rule in report.triggered_rules)


def test_deleted_lockfile_reduces_risk() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="package-lock.json",
                old_path="package-lock.json",
                status="D",
                additions=0,
                deletions=40,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert any(rule.id == "stability.lockfile_only" for rule in report.triggered_rules)


def test_docs_only_change_reduces_risk() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="docs/setup.md",
                old_path=None,
                status="M",
                additions=12,
                deletions=1,
            )
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert report.risk_level == "Low"


def test_get_rules_disabled_via_config() -> None:
    cfg = MergeRadarConfig(rule_overrides={"db.migration_changed": RuleOverride(enabled=False)})
    rules = get_rules(cfg)
    assert all(r.id != "db.migration_changed" for r in rules)


def test_get_rules_score_override() -> None:
    cfg = MergeRadarConfig(rule_overrides={"db.migration_changed": RuleOverride(score=5)})
    rules = get_rules(cfg)
    db_rule = next(r for r in rules if r.id == "db.migration_changed")
    assert db_rule.score == 5
    assert db_rule.title == "Database migration changed"


def test_score_override_affects_report() -> None:
    cfg = MergeRadarConfig(rule_overrides={"db.migration_changed": RuleOverride(score=5)})
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="alembic/versions/001_add_users.py",
                old_path=None,
                status="A",
                additions=30,
                deletions=0,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context, config=cfg)

    db_rule = next(r for r in report.triggered_rules if r.id == "db.migration_changed")
    assert db_rule.score == 5


def test_disabled_rule_not_in_report() -> None:
    cfg = MergeRadarConfig(rule_overrides={"stability.lockfile_only": RuleOverride(enabled=False)})
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="package-lock.json",
                old_path=None,
                status="M",
                additions=40,
                deletions=10,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context, config=cfg)

    assert not any(r.id == "stability.lockfile_only" for r in report.triggered_rules)


def test_custom_keywords_do_not_mutate_default_classification() -> None:
    cfg = MergeRadarConfig(keywords={"infra": ["kustomize"]})

    assert classify_file("kustomize/deployment.txt", config=cfg)[0] == "infra"
    assert classify_file("kustomize/deployment.txt")[0] == "unknown"


def test_large_diff_rule_triggers_on_churn_threshold() -> None:
    from mergeradar.rules.scope import LargeDiffRule

    rule = LargeDiffRule(id="scope.large_diff", title="Large diff size threshold exceeded", score=1)
    large_churn = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="M", additions=200, deletions=200)
        ],
    )
    assert rule.evaluate(large_churn) is not None

    small_churn = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="M", additions=5, deletions=3)
        ],
    )
    assert rule.evaluate(small_churn) is None


def test_large_diff_rule_triggers_on_file_count() -> None:
    from mergeradar.rules.scope import LargeDiffRule

    rule = LargeDiffRule(id="scope.large_diff", title="Large diff size threshold exceeded", score=1)
    many_files = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path=f"{i}.py", old_path=None, status="M", additions=1, deletions=0)
            for i in range(15)
        ],
    )
    assert rule.evaluate(many_files) is not None

    few_files = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path=f"{i}.py", old_path=None, status="M", additions=1, deletions=0)
            for i in range(14)
        ],
    )
    assert rule.evaluate(few_files) is None


def test_multiple_components_rule() -> None:
    from mergeradar.rules.scope import MultipleComponentsRule

    rule = MultipleComponentsRule(
        id="scope.multiple_components_changed",
        title="Multiple top-level components changed",
        score=2,
    )
    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [
                ChangedFile(path="app/a.py", old_path=None, status="M", additions=1, deletions=0),
                ChangedFile(path="api/b.py", old_path=None, status="M", additions=1, deletions=0),
                ChangedFile(path="infra/c.py", old_path=None, status="M", additions=1, deletions=0),
            ]
        ),
    )
    assert rule.evaluate(context) is not None

    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [
                ChangedFile(path="app/a.py", old_path=None, status="M", additions=1, deletions=0),
                ChangedFile(path="app/b.py", old_path=None, status="M", additions=1, deletions=0),
            ]
        ),
    )
    assert rule.evaluate(context) is None


def test_docs_only_rule_triggers() -> None:
    from mergeradar.rules.scope import DocsOnlyRule

    rule = DocsOnlyRule(id="stability.docs_only", title="Docs-only change", score=-2)
    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [ChangedFile(path="docs/setup.md", old_path=None, status="M", additions=5, deletions=0)]
        ),
    )
    triggered = rule.evaluate(context)
    assert triggered is not None
    assert triggered.score == -2


def test_docs_only_rule_does_not_trigger_when_mixed_with_code() -> None:
    from mergeradar.rules.scope import DocsOnlyRule

    rule = DocsOnlyRule(id="stability.docs_only", title="Docs-only change", score=-2)
    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [
                ChangedFile(
                    path="docs/setup.md", old_path=None, status="M", additions=5, deletions=0
                ),
                ChangedFile(
                    path="app/main.py", old_path=None, status="M", additions=2, deletions=0
                ),
            ]
        ),
    )
    assert rule.evaluate(context) is None


def test_tests_only_rule_triggers() -> None:
    from mergeradar.rules.scope import TestsOnlyRule

    rule = TestsOnlyRule(id="stability.tests_only", title="Tests-only change", score=-1)
    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [
                ChangedFile(
                    path="tests/test_main.py", old_path=None, status="M", additions=10, deletions=0
                ),
            ]
        ),
    )
    triggered = rule.evaluate(context)
    assert triggered is not None
    assert triggered.score == -1


def test_tests_only_rule_does_not_trigger_when_mixed() -> None:
    from mergeradar.rules.scope import TestsOnlyRule

    rule = TestsOnlyRule(id="stability.tests_only", title="Tests-only change", score=-1)
    context = build_context(
        repo_path=".",
        changed_files=enrich_changed_files(
            [
                ChangedFile(
                    path="tests/test_main.py", old_path=None, status="M", additions=5, deletions=0
                ),
                ChangedFile(
                    path="app/main.py", old_path=None, status="M", additions=2, deletions=0
                ),
            ]
        ),
    )
    assert rule.evaluate(context) is None


def test_risky_change_without_docs_triggers_no_docs_rule() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="app/auth/service.py",
                old_path=None,
                status="M",
                additions=10,
                deletions=0,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert any(rule.id == "evidence.no_docs_for_risky_change" for rule in report.triggered_rules)


def test_risky_change_with_docs_does_not_trigger_no_docs_rule() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="app/auth/service.py",
                old_path=None,
                status="M",
                additions=10,
                deletions=0,
            ),
            ChangedFile(
                path="docs/security.md",
                old_path=None,
                status="M",
                additions=5,
                deletions=0,
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    report = score_context(context)

    assert not any(
        rule.id == "evidence.no_docs_for_risky_change" for rule in report.triggered_rules
    )


def test_get_rules_includes_cross_dependency_rules() -> None:
    rules = get_rules()
    rule_ids = {r.id for r in rules}
    assert "deps.cross_change" in rule_ids
    assert "deps.wide_blast_radius" in rule_ids


def test_get_rules_includes_custom_rules() -> None:
    cfg = MergeRadarConfig(
        custom_rules=[
            CustomRuleDef(
                id="custom.secret_scanner",
                title="Secret scanner changed",
                score=3,
                category="infra",
                reason="Secret scanner configuration changed in",
            ),
        ]
    )
    rules = get_rules(cfg)
    custom = [r for r in rules if r.id == "custom.secret_scanner"]
    assert len(custom) == 1
    assert custom[0].score == 3


def test_get_rules_custom_rule_can_be_disabled() -> None:
    cfg = MergeRadarConfig(
        custom_rules=[
            CustomRuleDef(
                id="custom.secret_scanner",
                title="Secret scanner changed",
                score=3,
                category="infra",
                reason="Secret scanner configuration changed in",
            ),
        ],
        rule_overrides={"custom.secret_scanner": RuleOverride(enabled=False)},
    )
    rules = get_rules(cfg)
    assert all(r.id != "custom.secret_scanner" for r in rules) 
