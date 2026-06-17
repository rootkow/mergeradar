import json

import pytest
from typer.testing import CliRunner

from mergeradar.cli import app

runner = CliRunner()


def test_json_stdout_is_machine_readable() -> None:
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["risk_level"] == "High"


def test_head_without_base_is_rejected() -> None:
    result = runner.invoke(app, ["analyze", "--head", "HEAD"])

    assert result.exit_code == 1
    assert "--head requires --base" in result.stdout


def test_check_below_threshold_passes() -> None:
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "9"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["score"] < 9


def test_check_at_threshold_fails() -> None:
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "8"])

    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["score"] == 8


def test_env_var_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERGEDARAR_CHECK", "8")
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"])

    assert result.exit_code == 1


def test_env_var_check_overridden_by_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERGEDARAR_CHECK", "8")
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "9"])

    assert result.exit_code == 0


def test_verbose_shows_classification_reasons() -> None:
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--verbose"])

    assert result.exit_code == 0
    assert "auth" in result.stdout
    assert "infra" in result.stdout
