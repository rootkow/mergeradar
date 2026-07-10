import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mergeradar.cli import app
from mergeradar.models import ChangedFile

runner = CliRunner()


def test_explicit_ref_comparison_does_not_analyze_checked_out_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, bool] = {}

    monkeypatch.setattr("mergeradar.cli.is_git_repo", lambda repo: True)
    monkeypatch.setattr(
        "mergeradar.cli.load_changed_files",
        lambda **kwargs: [ChangedFile("app.py", None, "M", 1, 0)],
    )

    from mergeradar.cli import build_context as real_build_context

    def capture_build_context(**kwargs):
        captured["allow_filesystem_analysis"] = kwargs["allow_filesystem_analysis"]
        return real_build_context(**kwargs)

    monkeypatch.setattr("mergeradar.cli.build_context", capture_build_context)

    result = runner.invoke(
        app,
        [
            "analyze",
            "--repo",
            str(tmp_path),
            "--base",
            "main",
            "--head",
            "feature",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured["allow_filesystem_analysis"] is False


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


def test_env_var_check_invalid_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERGERADAR_CHECK", "not-a-number")
    result = runner.invoke(
        app, ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"]
    )

    assert result.exit_code == 0
    assert "Warning" in result.stderr
    assert "not-a-number" in result.stderr


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


def test_missing_diff_file_reported_without_traceback(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            str(tmp_path / "missing.diff"),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    assert "Failed to load diff" in result.stdout
    assert "Could not read diff file" in result.stdout
    assert "Traceback" not in result.stdout


def test_output_file_write_error_reported_without_traceback(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/docs-only.diff",
            "--format",
            "markdown",
            "--output",
            str(tmp_path / "missing-dir" / "report.md"),
        ],
    )

    assert result.exit_code == 1
    assert "Failed to write output file" in result.stdout
    assert "Traceback" not in result.stdout


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


def test_history_file_read_error_reported_without_traceback(tmp_path: Path) -> None:
    # A directory where a file is expected triggers IsADirectoryError on read
    history_dir = tmp_path / "history.json"
    history_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--history",
            str(history_dir),
        ],
    )

    assert result.exit_code == 1
    assert "Could not read history file" in result.stdout
    assert "Traceback" not in result.stdout


def test_history_file_write_error_reported_without_traceback(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--diff-file",
            "samples/auth-change.diff",
            "--format",
            "json",
            "--history",
            str(tmp_path / "missing-dir" / "history.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Could not write history file" in result.stdout
    assert "Traceback" not in result.stdout


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


def test_diff_file_does_not_read_matching_live_repo_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import a\n")
    diff_file = tmp_path / "saved.diff"
    diff_file.write_text(
        "\n".join(
            [
                "diff --git a/a.py b/a.py",
                "--- a/a.py",
                "+++ b/a.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
                "diff --git a/b.py b/b.py",
                "--- a/b.py",
                "+++ b/b.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "analyze",
            "--repo",
            str(tmp_path),
            "--diff-file",
            str(diff_file),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    triggered_rule_ids = {rule["id"] for rule in report["triggered_rules"]}
    assert "deps.cross_change" not in triggered_rule_ids


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
