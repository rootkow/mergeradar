from mergeradar.analysis.classifier import classify_file


def test_classify_auth_path() -> None:
    category, reason = classify_file("app/auth/service.py")
    assert category == "auth"
    assert reason


def test_classify_docs_path() -> None:
    category, reason = classify_file("docs/setup.md")
    assert category == "docs"
    assert reason


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
