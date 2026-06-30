from __future__ import annotations

import ast
import sys
from pathlib import Path


def _module_name_for_file(file_path: Path, repo_path: Path) -> str | None:
    """Return the absolute module name for a Python file under a known import root."""

    roots = sorted(_import_roots(repo_path), key=lambda root: len(root.parts), reverse=True)
    for root in roots:
        try:
            rel = file_path.resolve().relative_to(root.resolve())
        except ValueError:
            continue

        if rel.suffix != ".py":
            return None

        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            return None
        return ".".join(parts)

    return None


def _relative_import_base(node: ast.ImportFrom, file_path: Path, repo_path: Path) -> str | None:
    """Return the absolute base module for a relative import when possible."""

    current_module = _module_name_for_file(file_path, repo_path)
    if current_module is None:
        return None

    current_parts = current_module.split(".")
    package_parts = current_parts if file_path.name == "__init__.py" else current_parts[:-1]
    if node.level > len(package_parts) + 1:
        return None

    base_parts = package_parts[: len(package_parts) - node.level + 1]
    if not base_parts:
        return None
    return ".".join(base_parts)


def _add_if_resolvable_module(modules: set[str], module_name: str, repo_path: Path) -> None:
    """Add a module candidate only when it resolves to a local file."""

    if resolve_imports({module_name}, repo_path):
        modules.add(module_name)


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
                for alias in node.names:
                    if alias.name != "*":
                        modules.add(f"{node.module}.{alias.name}")

    return modules


def parse_imports_for_file(file_path: Path, repo_path: Path) -> set[str]:
    """Return imports from source, including relative imports resolved for a file."""

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return set()

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
                for alias in node.names:
                    if alias.name != "*":
                        _add_if_resolvable_module(modules, f"{node.module}.{alias.name}", repo_path)
            elif node.level > 0:
                base = _relative_import_base(node, file_path, repo_path)
                if base is None:
                    continue
                if node.module:
                    modules.add(f"{base}.{node.module}")
                    for alias in node.names:
                        if alias.name != "*":
                            _add_if_resolvable_module(
                                modules, f"{base}.{node.module}.{alias.name}", repo_path
                            )
                else:
                    for alias in node.names:
                        if alias.name != "*":
                            modules.add(f"{base}.{alias.name}")

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

    modules = parse_imports_for_file(file_path, repo_path)
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
