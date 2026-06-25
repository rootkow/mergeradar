from pathlib import Path

from mergeradar.utils.imports import (
    get_changed_file_local_imports,
    get_local_imports,
    parse_imports,
    resolve_imports,
)


def test_parse_imports_finds_top_level_names() -> None:
    content = "import os\nimport json\nfrom pathlib import Path\n"
    modules = parse_imports(content)
    assert "os" in modules
    assert "json" in modules
    assert "pathlib" in modules


def test_parse_imports_preserves_dotted_import() -> None:
    content = "import os.path\n"
    modules = parse_imports(content)
    assert modules == {"os.path"}


def test_parse_imports_empty_on_syntax_error() -> None:
    modules = parse_imports("def foo(:")
    assert modules == set()


def test_parse_imports_ignores_no_imports() -> None:
    modules = parse_imports("x = 1\ny = 2\n")
    assert modules == set()


def test_resolve_imports_filters_stdlib() -> None:
    resolved = resolve_imports({"os", "json", "pathlib"}, Path("/nonexistent"))
    assert resolved == set()


def test_resolve_imports_resolves_local_module(tmp_path: Path) -> None:
    (tmp_path / "myapp.py").touch()
    resolved = resolve_imports({"myapp"}, tmp_path)
    assert len(resolved) == 1
    assert list(resolved)[0].resolve() == (tmp_path / "myapp.py").resolve()


def test_resolve_imports_resolves_package(tmp_path: Path) -> None:
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").touch()
    resolved = resolve_imports({"mypkg"}, tmp_path)
    assert len(resolved) == 1
    assert list(resolved)[0].resolve() == (tmp_path / "mypkg" / "__init__.py").resolve()


def test_resolve_imports_finds_both_module_and_package(tmp_path: Path) -> None:
    (tmp_path / "utils.py").touch()
    pkg = tmp_path / "utils"
    pkg.mkdir()
    (pkg / "__init__.py").touch()
    resolved = resolve_imports({"utils"}, tmp_path)
    assert len(resolved) == 2
    assert (tmp_path / "utils.py").resolve() in resolved
    assert (tmp_path / "utils" / "__init__.py").resolve() in resolved


def test_get_local_imports_returns_empty_for_missing_file(tmp_path: Path) -> None:
    imports = get_local_imports(tmp_path / "nonexistent.py", tmp_path)
    assert imports == set()


def test_get_local_imports_returns_resolved_imports(tmp_path: Path) -> None:
    (tmp_path / "mylib.py").touch()
    source = tmp_path / "app.py"
    source.write_text("import mylib\n")
    imports = get_local_imports(source, tmp_path)
    assert len(imports) == 1
    assert list(imports)[0].resolve() == (tmp_path / "mylib.py").resolve()


def test_get_changed_file_local_imports_finds_cross_deps(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("")
    changed = ["a.py", "b.py"]
    dep_map = get_changed_file_local_imports(changed, str(tmp_path))
    assert "a.py" in dep_map
    assert dep_map["a.py"] == {"b.py"}
    assert dep_map["b.py"] == set()


def test_get_changed_file_local_imports_ignores_outside_repo(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").touch()
    outside = tmp_path / "outside"
    outside.mkdir()
    changed = ["a.py", str(outside / "b.py")]
    dep_map = get_changed_file_local_imports(changed, str(tmp_path))
    assert "a.py" in dep_map
    assert dep_map["a.py"] == set()


def test_get_changed_file_local_imports_skips_missing_files(tmp_path: Path) -> None:
    dep_map = get_changed_file_local_imports(["missing.py"], str(tmp_path))
    assert dep_map == {}


def test_parse_imports_from_import() -> None:
    content = "from collections.abc import Iterator\n"
    modules = parse_imports(content)
    assert "collections.abc" in modules


def test_parse_imports_relative_from_import() -> None:
    content = "from . import sibling\n"
    modules = parse_imports(content)
    assert modules == set()


def test_resolve_imports_multiple_candidates(tmp_path: Path) -> None:
    (tmp_path / "alpha.py").touch()
    (tmp_path / "beta.py").touch()
    resolved = resolve_imports({"alpha", "beta", "gamma"}, tmp_path)
    assert len(resolved) == 2


def test_resolve_imports_resolves_dotted_module(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").touch()
    (pkg / "module.py").touch()

    resolved = resolve_imports({"pkg.module"}, tmp_path)

    assert resolved == {(tmp_path / "pkg" / "module.py").resolve()}


def test_resolve_imports_resolves_src_layout_package(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").touch()
    (pkg / "config.py").touch()

    resolved = resolve_imports({"mypkg.config"}, tmp_path)

    assert resolved == {(tmp_path / "src" / "mypkg" / "config.py").resolve()}


def test_get_changed_file_local_imports_finds_src_layout_cross_deps(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").touch()
    (pkg / "app.py").write_text("from mypkg.config import Settings\n")
    (pkg / "config.py").write_text("class Settings: ...\n")

    changed = ["src/mypkg/app.py", "src/mypkg/config.py"]
    dep_map = get_changed_file_local_imports(changed, str(tmp_path))

    assert dep_map["src/mypkg/app.py"] == {"src/mypkg/config.py"}
