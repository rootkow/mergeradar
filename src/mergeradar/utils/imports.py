from __future__ import annotations

import ast
import sys
from pathlib import Path


def parse_imports(content: str) -> set[str]:
    """Return the set of absolute module names imported in Python source."""

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                modules.add(node.module)

    return modules


def _module_to_candidates(module_name: str) -> list[str]:
    """Return file-path candidates for a module name."""

    module_path = module_name.replace(".", "/")
    candidates = [f"{module_path}.py"]
    if module_name != "__init__":
        candidates.append(f"{module_path}/__init__.py")
    return candidates


def _import_roots(repo_path: Path) -> list[Path]:
    """Return repository roots that can contain importable local modules."""

    roots = [repo_path]
    src = repo_path / "src"
    if src.is_dir():
        roots.append(src)
    return roots


def resolve_imports(modules: set[str], repo_path: Path) -> set[Path]:
    """Resolve module names to existing file paths under repo_path."""

    resolved: set[Path] = set()
    for mod in sorted(modules):
        if mod.split(".")[0] in _STDLIB_MODULES:
            continue
        for root in _import_roots(repo_path):
            for candidate in _module_to_candidates(mod):
                candidate_path = root / candidate
                if candidate_path.exists():
                    resolved.add(candidate_path.resolve())

    return resolved


def get_local_imports(file_path: Path, repo_path: Path) -> set[Path]:
    """Return paths to local files imported by a given Python file.

    Only works if the file exists on disk.
    """

    if not file_path.exists():
        return set()

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return set()

    modules = parse_imports(content)
    return resolve_imports(modules, repo_path)


def get_changed_file_local_imports(
    changed_file_paths: list[str], repo_path_str: str
) -> dict[str, set[str]]:
    """For each changed file, return which other changed files it imports.

    Returns a mapping from changed file path → set of changed file paths it depends on.
    Only considers dependencies between files in the changed set.
    """

    repo = Path(repo_path_str)
    dep_map: dict[str, set[str]] = {}

    for cf_path in changed_file_paths:
        abs_path = repo / cf_path
        if not abs_path.exists():
            continue
        local_imports = get_local_imports(abs_path, repo)
        deps: set[str] = set()
        for resolved in local_imports:
            try:
                rel = resolved.relative_to(repo)
            except ValueError:
                continue
            rel_str = str(rel.as_posix())
            if rel_str in changed_file_paths:
                deps.add(rel_str)
        dep_map[cf_path] = deps

    return dep_map


_STDLIB_MODULES: frozenset[str] = sys.stdlib_module_names
