from mergeradar.analysis.classifier import classify_file


def test_classify_auth_path() -> None:
    assert classify_file("app/auth/service.py") == "auth"


def test_classify_docs_path() -> None:
    assert classify_file("docs/setup.md") == "docs"


def test_classify_infra_path() -> None:
    assert classify_file(".github/workflows/deploy.yml") == "infra"
