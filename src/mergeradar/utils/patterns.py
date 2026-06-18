from __future__ import annotations

from pathlib import PurePosixPath

CODE_EXTENSIONS = {".py", ".ts", ".js", ".go", ".java", ".rs", ".kt", ".cs"}
DOC_EXTENSIONS = {".md", ".rst", ".adoc"}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".toml", ".ini", ".env", ".cfg"}
INFRA_FILENAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
AUTH_KEYWORDS = {
    "auth",
    "jwt",
    "login",
    "middleware",
    "oauth",
    "permission",
    "permissions",
    "rbac",
    "session",
}
API_KEYWORDS = {"route", "routes", "api", "openapi", "swagger", "endpoint", "handler"}
MIGRATION_KEYWORDS = {"migrations", "alembic", "schema.sql", "migration"}
TEST_KEYWORDS = {"tests", "test", "spec"}
INFRA_KEYWORDS = {"helm", "k8s", "terraform", ".github/workflows", "deploy", "docker", "infra"}
CONFIG_KEYWORDS = {"config", "settings", "values", ".env"}
DEP_FILENAMES = {"requirements.txt", "requirements.in", "Pipfile", "Pipfile.lock", "poetry.lock"}
DEP_KEYWORDS = {
    "Cargo.lock",
    "Cargo.toml",
    "Gemfile",
    "Gemfile.lock",
    "build.gradle",
    "dependencies",
    "go.mod",
    "go.sum",
    "package-lock.json",
    "package.json",
    "yarn.lock",
}
LOCKFILE_FILENAMES = {
    "Cargo.lock",
    "Gemfile.lock",
    "Pipfile.lock",
    "go.sum",
    "package-lock.json",
    "poetry.lock",
    "yarn.lock",
}

CATEGORY_KEYWORD_MAP: dict[str, set[str]] = {
    "auth": AUTH_KEYWORDS,
    "api": API_KEYWORDS,
    "database": MIGRATION_KEYWORDS,
    "tests": TEST_KEYWORDS,
    "infra": INFRA_KEYWORDS,
    "config": CONFIG_KEYWORDS,
    "deps": DEP_KEYWORDS,
}


def build_keyword_map(overrides: dict[str, list[str]] | None = None) -> dict[str, set[str]]:
    """Return per-run keyword sets with user overrides merged in."""

    keyword_map = {
        category: {keyword.lower() for keyword in keywords}
        for category, keywords in CATEGORY_KEYWORD_MAP.items()
    }

    if overrides is None:
        return keyword_map

    for category, extra in overrides.items():
        target = keyword_map.get(category)
        if target is not None:
            target.update(keyword.lower() for keyword in extra)

    return keyword_map


def normalized_parts(path: str) -> tuple[str, ...]:
    """Return lowercase path parts after normalizing separators."""

    clean = path.replace("\\", "/")
    return tuple(part.lower() for part in PurePosixPath(clean).parts)


def top_level_component(path: str) -> str | None:
    """Return the normalized top-level path component, if present."""

    parts = normalized_parts(path)
    return parts[0] if parts else None
