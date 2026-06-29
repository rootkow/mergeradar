from pathlib import Path

from mergeradar.analysis.context_builder import build_context
from mergeradar.models import ChangedFile
from mergeradar.rules.dependency import CrossChangeDepsRule, WideBlastRadiusRule


def test_cross_change_deps_rule_returns_none_when_no_py_files() -> None:
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path="readme.md", old_path=None, status="M", additions=1, deletions=0),
        ],
    )
    assert rule.evaluate(context) is None


def test_cross_change_deps_rule_requires_at_least_two_py_files() -> None:
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="M", additions=1, deletions=0),
        ],
    )
    assert rule.evaluate(context) is None


def test_cross_change_deps_rule_triggers_when_files_import_each_other(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("")
    (tmp_path / "c.py").write_text("import a\n")
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="M", additions=2, deletions=0),
            ChangedFile(path="b.py", old_path=None, status="M", additions=1, deletions=0),
            ChangedFile(path="c.py", old_path=None, status="M", additions=1, deletions=0),
        ],
    )
    triggered = rule.evaluate(context)
    assert triggered is not None
    assert triggered.id == "deps.cross_change"
    assert "a.py" in triggered.reason


def test_cross_change_deps_rule_triggers_for_src_layout_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").touch()
    (pkg / "app.py").write_text("from mypkg.config import Settings\n")
    (pkg / "worker.py").write_text("from mypkg.config import Settings\n")
    (pkg / "config.py").write_text("class Settings: ...\n")
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(
                path="src/mypkg/app.py", old_path=None, status="M", additions=1, deletions=0
            ),
            ChangedFile(
                path="src/mypkg/worker.py", old_path=None, status="M", additions=1, deletions=0
            ),
            ChangedFile(
                path="src/mypkg/config.py", old_path=None, status="M", additions=1, deletions=0
            ),
        ],
    )

    triggered = rule.evaluate(context)

    assert triggered is not None
    assert "src/mypkg/app.py" in triggered.reason
    assert "src/mypkg/app.py" in triggered.paths


def test_cross_change_deps_rule_triggers_for_relative_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").touch()
    (pkg / "app.py").write_text("from .config import Settings\n")
    (pkg / "worker.py").write_text("from . import config\n")
    (pkg / "config.py").write_text("class Settings: ...\n")
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="pkg/app.py", old_path=None, status="M", additions=1, deletions=0),
            ChangedFile(path="pkg/worker.py", old_path=None, status="M", additions=1, deletions=0),
            ChangedFile(path="pkg/config.py", old_path=None, status="M", additions=1, deletions=0),
        ],
    )

    triggered = rule.evaluate(context)

    assert triggered is not None
    assert triggered.paths == ["pkg/app.py", "pkg/worker.py"]


def test_cross_change_deps_rule_skips_deleted_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="D", additions=0, deletions=2),
        ],
    )
    assert rule.evaluate(context) is None


def test_cross_change_deps_rule_skips_when_filesystem_analysis_disabled(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import a\n")
    rule = CrossChangeDepsRule(
        id="deps.cross_change", title="Cross-dependencies", score=2
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="M", additions=1, deletions=0),
            ChangedFile(path="b.py", old_path=None, status="M", additions=1, deletions=0),
        ],
        allow_filesystem_analysis=False,
    )
    assert rule.evaluate(context) is None


def test_wide_blast_radius_rule_skips_non_py_files() -> None:
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=".",
        changed_files=[
            ChangedFile(path="readme.md", old_path=None, status="M", additions=1, deletions=0),
        ],
    )
    assert rule.evaluate(context) is None


def test_wide_blast_radius_rule_skips_deleted_files(tmp_path: Path) -> None:
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="a.py", old_path=None, status="D", additions=0, deletions=2),
        ],
    )
    assert rule.evaluate(context) is None


def test_wide_blast_radius_rule_triggers_when_many_internal_imports(tmp_path: Path) -> None:
    for mod in ["one", "two", "three", "four", "five"]:
        (tmp_path / f"{mod}.py").touch()
    source = tmp_path / "main.py"
    source.write_text("import one\nimport two\nimport three\nimport four\nimport five\n")
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="main.py", old_path=None, status="M", additions=5, deletions=0),
        ],
    )
    triggered = rule.evaluate(context)
    assert triggered is not None
    assert triggered.id == "deps.wide_blast_radius"


def test_wide_blast_radius_rule_does_not_trigger_with_few_imports(tmp_path: Path) -> None:
    for mod in ["one", "two"]:
        (tmp_path / f"{mod}.py").touch()
    source = tmp_path / "main.py"
    source.write_text("import one\nimport two\n")
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="main.py", old_path=None, status="M", additions=2, deletions=0),
        ],
    )
    assert rule.evaluate(context) is None


def test_wide_blast_radius_rule_ignores_stdlib_imports(tmp_path: Path) -> None:
    source = tmp_path / "main.py"
    source.write_text("import os\nimport sys\nimport json\nimport re\nimport math\n")
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="main.py", old_path=None, status="M", additions=5, deletions=0),
        ],
    )
    assert rule.evaluate(context) is None


def test_wide_blast_radius_rule_skips_when_filesystem_analysis_disabled(tmp_path: Path) -> None:
    for mod in ["one", "two", "three", "four", "five"]:
        (tmp_path / f"{mod}.py").touch()
    (tmp_path / "main.py").write_text(
        "import one\nimport two\nimport three\nimport four\nimport five\n"
    )
    rule = WideBlastRadiusRule(
        id="deps.wide_blast_radius", title="Wide blast radius", score=1
    )
    context = build_context(
        repo_path=str(tmp_path),
        changed_files=[
            ChangedFile(path="main.py", old_path=None, status="M", additions=5, deletions=0),
        ],
        allow_filesystem_analysis=False,
    )
    assert rule.evaluate(context) is None
