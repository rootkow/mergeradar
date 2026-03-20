from __future__ import annotations

from pathlib import PurePosixPath

# TODO:
# - Make these configurable (e.g. YAML file within the target repo)
# - These will integrate with a model later
CODE_EXTENSIONS = {".py", ".ts", ".js", ".go", ".java", ".rs", ".kt", ".cs"}
DOC_EXTENSIONS = {".md", ".rst", ".adoc"}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".toml", ".ini", ".env", ".cfg"}
INFRA_FILENAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
AUTH_KEYWORDS = {"auth", "permission", "permissions", "middleware", "session", "jwt", "oauth", "rbac", "login"}
API_KEYWORDS = {"route", "routes", "api", "openapi", "swagger", "endpoint", "handler"}
MIGRATION_KEYWORDS = {"migrations", "alembic", "schema.sql", "migration"}
TEST_KEYWORDS = {"tests", "test", "spec"}
INFRA_KEYWORDS = {"helm", "k8s", "terraform", ".github/workflows", "deploy", "docker", "infra"}
CONFIG_KEYWORDS = {"config", "settings", "values", ".env"}


def normalized_parts(path: str) -> tuple[str, ...]:
    """Normalize the path to use forward slashes and return the parts in lowercase.

    Args:
        path (str): The file path to normalize.

    Returns:
        tuple[str, ...]: The normalized path parts in lowercase.
    """

    clean = path.replace("\\", "/")
    return tuple(part.lower() for part in PurePosixPath(clean).parts)


def top_level_component(path: str) -> str | None:
    """Get the top-level component of the given path.

    Args:
        path (str): The file path to analyze.

    Returns:
        str | None: The top-level component of the path, or None if the path is empty.
    """

    parts = normalized_parts(path)
    return parts[0] if parts else None
