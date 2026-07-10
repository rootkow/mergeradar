from mergeradar.analysis.classifier import (
    _matches_path_keyword,
    classify_file,
    enrich_changed_files,
)
from mergeradar.models import ChangedFile


def test_matches_path_keyword_finds_keyword_in_path_parts() -> None:
    assert _matches_path_keyword("app/auth/service.py", {"auth"}) is True


def test_matches_path_keyword_finds_filename_tokens() -> None:
    assert _matches_path_keyword("app/jwt_service.py", {"jwt"}) is True


def test_matches_path_keyword_slash_keyword() -> None:
    assert _matches_path_keyword(".github/workflows/deploy.yml", {".github/workflows"}) is True


def test_matches_path_keyword_slash_keyword_requires_path_prefix() -> None:
    assert _matches_path_keyword("src/notapp/authentic/file.py", {"app/auth"}) is False


def test_matches_path_keyword_dot_keyword() -> None:
    assert _matches_path_keyword("some/Cargo.lock", {"Cargo.lock"}) is True


def test_matches_path_keyword_no_match() -> None:
    assert _matches_path_keyword("app/author.py", {"auth"}) is False


def test_matches_path_keyword_empty_path() -> None:
    assert _matches_path_keyword("", {"auth"}) is False


def test_enrich_changed_files_adds_classification() -> None:
    files = enrich_changed_files(
        [ChangedFile(path="app/auth/login.py", old_path=None, status="M", additions=5, deletions=2)]
    )
    assert files[0].category == "auth"
    assert files[0].classification_reason is not None
    assert files[0].top_level_component == "app"


def test_enrich_changed_files_returns_same_list_instance() -> None:
    original = [
        ChangedFile(path="docs/readme.md", old_path=None, status="A", additions=1, deletions=0)
    ]
    result = enrich_changed_files(original)
    assert result is original


def test_enrich_changed_files_with_config() -> None:
    from mergeradar.config import MergeRadarConfig

    cfg = MergeRadarConfig(keywords={"infra": ["kustomize"]})
    files = enrich_changed_files(
        [
            ChangedFile(
                path="kustomize/deployment.yaml",
                old_path=None,
                status="M",
                additions=1,
                deletions=0,
            )
        ],
        config=cfg,
    )
    assert files[0].category == "infra"


def test_classify_auth_path() -> None:
    category, reason = classify_file("app/auth/service.py")
    assert category == "auth"
    assert reason


def test_classify_docs_path() -> None:
    category, reason = classify_file("docs/setup.md")
    assert category == "docs"
    assert reason


def test_migration_named_tests_and_docs_keep_their_evidence_categories() -> None:
    test_category, _ = classify_file("tests/test_migrations.py")
    docs_category, _ = classify_file("docs/migrations.md")

    assert test_category == "tests"
    assert docs_category == "docs"


def test_classify_infra_path() -> None:
    category, reason = classify_file(".github/workflows/deploy.yml")
    assert category == "infra"
    assert reason
    category, reason = classify_file("Dockerfile")
    assert category == "infra"
    assert reason


def test_keyword_substrings_do_not_trigger_risky_categories() -> None:
    category, reason = classify_file("src/author.py")
    assert category == "app"
    assert reason
    category, reason = classify_file("src/capital.py")
    assert category == "app"
    assert reason
    category, reason = classify_file("src/contest.py")
    assert category == "app"
    assert reason


def test_filename_tokens_trigger_categories() -> None:
    category, reason = classify_file("src/auth_service.py")
    assert category == "auth"
    assert reason
    category, reason = classify_file("src/api_handler.py")
    assert category == "api"
    assert reason
    category, reason = classify_file("src/user_test.py")
    assert category == "tests"
    assert reason


def test_openapi_and_swagger_specs_are_classified_as_api() -> None:
    openapi_category, _ = classify_file("openapi.yaml")
    swagger_category, _ = classify_file("swagger.json")

    assert openapi_category == "api"
    assert swagger_category == "api"


def test_classify_dependency_paths() -> None:
    category, reason = classify_file("requirements.txt")
    assert category == "deps"
    assert reason
    category, reason = classify_file("package.json")
    assert category == "deps"
    assert reason
    category, reason = classify_file("Cargo.toml")
    assert category == "deps"
    assert reason
    category, reason = classify_file("go.mod")
    assert category == "deps"
    assert reason
    category, reason = classify_file("path/to/Pipfile")
    assert category == "deps"
    assert reason
