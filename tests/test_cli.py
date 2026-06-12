import json

from typer.testing import CliRunner

from mergeradar.cli import app

runner = CliRunner()


def test_json_stdout_is_machine_readable() -> None:
    result = runner.invoke(
        app,
        ["analyze", "--diff-file", "samples/auth-change.diff", "--format", "json"],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["risk_level"] == "High"


def test_head_without_base_is_rejected() -> None:
    result = runner.invoke(app, ["analyze", "--head", "HEAD"])

    assert result.exit_code == 1
    assert "--head requires --base" in result.stdout
