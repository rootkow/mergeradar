from mergeradar.analysis.classifier import classify_file


def test_classify_auth_path() -> None:
    assert classify_file("app/auth/service.py") == "auth"


def test_classify_docs_path() -> None:
    assert classify_file("docs/setup.md") == "docs"


def test_classify_infra_path() -> None:
    assert classify_file(".github/workflows/deploy.yml") == "infra"
    assert classify_file("Dockerfile") == "infra"


def test_keyword_substrings_do_not_trigger_risky_categories() -> None:
    assert classify_file("src/author.py") == "app"
    assert classify_file("src/capital.py") == "app"
    assert classify_file("src/contest.py") == "app"


def test_filename_tokens_trigger_categories() -> None:
    assert classify_file("src/auth_service.py") == "auth"
    assert classify_file("src/api_handler.py") == "api"
    assert classify_file("src/user_test.py") == "tests"
