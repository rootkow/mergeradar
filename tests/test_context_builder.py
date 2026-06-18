from mergeradar.analysis.classifier import enrich_changed_files
from mergeradar.analysis.context_builder import build_context, has_risky_changes
from mergeradar.models import ChangedFile


def test_build_context_sets_categories() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(
                path="app/auth/login.py", old_path=None, status="M", additions=5, deletions=2
            ),
            ChangedFile(path="docs/readme.md", old_path=None, status="A", additions=3, deletions=0),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    assert "auth" in context.categories_touched
    assert "docs" in context.categories_touched
    assert context.has_auth_changes is True
    assert context.has_doc_changes is True
    assert context.has_test_changes is False
    assert context.has_migration_changes is False


def test_build_context_totals() -> None:
    changed_files = [
        ChangedFile(path="a.py", old_path=None, status="M", additions=5, deletions=2),
        ChangedFile(path="b.py", old_path=None, status="A", additions=10, deletions=0),
    ]
    context = build_context(repo_path=".", changed_files=changed_files)
    assert context.total_files_changed == 2
    assert context.total_additions == 15
    assert context.total_deletions == 2


def test_build_context_components() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(path="app/service.py", old_path=None, status="M", additions=1, deletions=1),
            ChangedFile(path="api/routes.py", old_path=None, status="A", additions=2, deletions=0),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    assert context.components_touched == {"app", "api"}


def test_build_context_no_changes() -> None:
    context = build_context(repo_path=".", changed_files=[])
    assert context.categories_touched == set()
    assert context.components_touched == set()
    assert context.total_files_changed == 0
    assert context.total_additions == 0
    assert context.total_deletions == 0


def test_has_risky_changes_returns_true_for_risky_category() -> None:
    changed_files = enrich_changed_files(
        [ChangedFile(path="app/auth/login.py", old_path=None, status="M", additions=1, deletions=0)]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    assert has_risky_changes(context) is True


def test_has_risky_changes_false_for_safe_categories() -> None:
    changed_files = enrich_changed_files(
        [
            ChangedFile(path="docs/readme.md", old_path=None, status="M", additions=1, deletions=0),
            ChangedFile(
                path="app/test_main.py", old_path=None, status="A", additions=10, deletions=0
            ),
        ]
    )
    context = build_context(repo_path=".", changed_files=changed_files)
    assert has_risky_changes(context) is False


def test_has_risky_changes_false_for_unknown() -> None:
    context = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(
                path="random.log",
                old_path=None,
                status="M",
                additions=1,
                deletions=0,
                category="unknown",
            ),
        ],
    )
    assert has_risky_changes(context) is False
