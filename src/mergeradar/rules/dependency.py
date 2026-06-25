from __future__ import annotations

from pathlib import Path

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule
from mergeradar.utils.imports import (
    get_changed_file_local_imports,
    parse_imports,
    resolve_imports,
)


class CrossChangeDepsRule(SimpleRule):
    """Detect cross-dependencies between changed files."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        py_changed = [
            cf.path
            for cf in context.changed_files
            if cf.path.endswith(".py") and cf.status != "D"
        ]
        if not py_changed or len(py_changed) < 2:
            return None

        dep_map = get_changed_file_local_imports(py_changed, context.repo_path)
        cross_count = sum(1 for deps in dep_map.values() if deps)
        if cross_count < 2:
            return None

        paths_with_deps = sorted(
            path for path, deps in dep_map.items() if deps
        )
        return self.trigger(
            f"Changed files import from other changed files: "
            f"{', '.join(paths_with_deps[:3])}"
        )


class WideBlastRadiusRule(SimpleRule):
    """Detect changes that import many distinct internal modules.

    Reads every changed Python file from disk and parses its imports via
    ``ast.parse``. This can be slow for large files or PRs touching many
    files, and results are not cached between rule evaluations.
    """

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        repo = Path(context.repo_path)
        total_internal_imports: set[Path] = set()
        py_files_checked = 0

        for cf in context.changed_files:
            if not cf.path.endswith(".py") or cf.status == "D":
                continue
            abs_path = repo / cf.path
            if not abs_path.exists():
                continue
            modules = parse_imports(
                abs_path.read_text(encoding="utf-8", errors="replace")
            )
            resolved = resolve_imports(modules, repo)
            total_internal_imports.update(resolved)
            py_files_checked += 1

        if py_files_checked == 0:
            return None

        if len(total_internal_imports) < 5:
            return None

        return self.trigger(
            f"Changed files import {len(total_internal_imports)} distinct "
            f"internal modules, indicating a wide potential blast radius."
        )
