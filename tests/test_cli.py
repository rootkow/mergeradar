import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mergeradar.cli import app

runner = CliRunner()


def test_json_stdout_is_machine_readable() -> None:
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"]
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["risk_level"] == "High"


def test_head_without_base_is_rejected() -> None:
    result = runner.invoke(app, ["analyze", "--head", "HEAD"])

    assert result.exit_code == 1
    assert "--head requires --base" in result.stdout


def test_check_below_threshold_passes() -> None:
    result = runner.invoke(
        app,
        ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "9"],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["score"] < 9


def test_check_at_threshold_fails() -> None:
    result = runner.invoke(
        app,
        ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "8"],
    )

    assert result.exit_code == 5
    report = json.loads(result.stdout)
    assert report["score"] == 8


def test_env_var_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERGERADAR_CHECK", "8")
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"]
    )

    assert result.exit_code == 5


def test_env_var_check_overridden_by_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERGERADAR_CHECK", "8")
    result = runner.invoke(
        app,
        ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json", "--check", "9"],
    )

    assert result.exit_code == 0


def test_verbose_shows_classification_reasons() -> None:
    result = runner.invoke(app, ["analyze", "--diff-file", "samples/auth-change.diff", "--verbose"])

    assert result.exit_code == 0
    assert "auth" in result.stdout
    assert "infra" in result.stdout


def test_config_flag_is_accepted(tmp_path: Path) -> None:
    config_file = tmp_path / "test.toml"
    config_file.write_text('[keywords]\ninfra = ["kustomize"]\n')

    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 0


def test_config_without_risky_categories_keeps_default_evidence_rules(tmp_path: Path) -> None:
    config_file = tmp_path / "test.toml"
    config_file.write_text('[keywords]\ninfra = ["kustomize"]\n')

    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    triggered_rule_ids = {rule["id"] for rule in report["triggered_rules"]}
    assert "evidence.no_tests_for_risky_change" in triggered_rule_ids
    assert "evidence.no_docs_for_risky_change" in triggered_rule_ids


def test_invalid_config_reported(tmp_path: Path) -> None:
    config_file = tmp_path / "bad.toml"
    config_file.write_text("{{broken")

    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 1
    assert "Failed to parse" in result.stdout


def test_missing_config_path_reported(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--config",
            str(tmp_path / "missing.toml"),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid config file" in result.stdout
    assert "does not exist" in result.stdout


def test_unsupported_format_rejected() -> None:
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "html"]
    )
    assert result.exit_code == 2
    assert "Unsupported format" in result.stdout


def test_output_file_writes_report(tmp_path: Path) -> None:
    output_file = tmp_path / "report.md"
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "markdown",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.read_text().startswith("# MergeRadar Report")


def test_output_file_writes_json(tmp_path: Path) -> None:
    output_file = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/docs-only.diff",
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text())
    assert report["risk_level"] == "Low"


def test_sarif_format_is_valid_sarif() -> None:
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "sarif"]
    )

    assert result.exit_code == 0
    doc = json.loads(result.stdout)
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["tool"]["driver"]["name"] == "MergeRadar"
    assert "results" in doc["runs"][0]
    assert doc["runs"][0]["properties"]["riskLevel"] == "High"


def test_non_git_repo_rejected(tmp_path: Path) -> None:
    result = runner.invoke(app, ["analyze", "--repo", str(tmp_path)])
    assert result.exit_code == 3
    assert "is not a git repository" in " ".join(result.stdout.split())


def test_format_annotations_produces_workflow_commands() -> None:
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "annotations"]
    )

    assert result.exit_code == 0
    assert "::warning" in result.stdout
    assert "::notice" not in result.stdout
    for line in result.stdout.strip().split("\n"):
        assert line.startswith("::")


def test_history_flag_writes_history_file(tmp_path: Path) -> None:
    history_file = tmp_path / "history.json"
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--history",
            str(history_file),
        ],
    )

    assert result.exit_code == 0
    assert history_file.exists()

    data = json.loads(history_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["score"] == 8
    assert data[0]["risk_level"] == "High"


def test_history_flag_appends_subsequent_runs(tmp_path: Path) -> None:
    history_file = tmp_path / "history.json"
    for _ in range(3):
        runner.invoke(
            app,
            [
                "analyze",
                "--diff-file",
                "samples/auth-change.diff",
                "--format",
                "json",
                "--history",
                str(history_file),
            ],
        )

    data = json.loads(history_file.read_text())
    assert len(data) == 3


def test_history_flag_with_diff_file_has_risk_trend(tmp_path: Path) -> None:
    history_file = tmp_path / "history.json"
    history_file.write_text(
        json.dumps(
            [
                {
                    "score": 5,
                    "risk_level": "Medium",
                    "commit": "",
                    "timestamp": "2025-01-01T00:00:00",
                }
            ]
        )
    )
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--history",
            str(history_file),
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["metadata"]["risk_trend"] == "increasing"


def test_invalid_config_score_reported(tmp_path: Path) -> None:
    config_file = tmp_path / "bad-score.toml"
    config_file.write_text('[rules."db.migration_changed"]\nscore = "high"\n')

    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--config",
            str(config_file),
        ],
    )

    assert result.exit_code == 1
    assert "Invalid config file" in result.stdout
    assert "score must be an integer" in result.stdout
