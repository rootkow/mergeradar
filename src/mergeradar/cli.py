from __future__ import annotations

import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mergeradar.analysis.classifier import enrich_changed_files
from mergeradar.analysis.context_builder import build_context
from mergeradar.analysis.scorer import score_context
from mergeradar.config import ConfigError, load_config
from mergeradar.git.diff_loader import (
    DiffLoaderError,
    load_changed_files,
    load_changed_files_from_diff_file,
)
from mergeradar.git.repo_inspector import is_git_repo
from mergeradar.renderers.annotations import render_annotations
from mergeradar.renderers.markdown import render_markdown
from mergeradar.renderers.sarif import render_sarif
from mergeradar.utils.history import append_history, compute_trend, load_history

app = typer.Typer(help="Blast-radius and risk analysis for pull requests.")
console = Console()


@app.callback()
def main() -> None:
    """Define the MergeRadar command group."""


@app.command()
def analyze(
    repo: Annotated[Path, typer.Option("--repo", help="Path to the local git repository.")] = Path(
        "."
    ),
    base: Annotated[str | None, typer.Option("--base", help="Base ref to diff from.")] = None,
    head: Annotated[str | None, typer.Option("--head", help="Head ref to diff to.")] = None,
    diff_file: Annotated[
        Path | None, typer.Option("--diff-file", help="Path to a saved unified diff file.")
    ] = None,
    config: Annotated[
        Path | None, typer.Option("--config", help="Path to a .mergeradar.toml config file.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Optional file path to write the report.")
    ] = None,
    history_file: Annotated[
        Path | None,
        typer.Option("--history", help="Path to a history JSON file for tracking score trends."),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option(
            "--format", help="Output format: markdown, json, sarif, or annotations."
        ),
    ] = "markdown",
    check: Annotated[
        int | None,
        typer.Option(
            "--check", help="Exit non-zero if risk score meets or exceeds this threshold."
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Print extra debugging context.")
    ] = False,
) -> None:
    """Analyze a repository diff or saved diff and render its risk report."""

    try:
        if diff_file is not None:
            changed_files = load_changed_files_from_diff_file(diff_file)
            repo_label = str(diff_file)
        else:
            if not is_git_repo(repo):
                console.print(f"[red]{repo} is not a git repository.[/red]")
                raise typer.Exit(code=3)
            changed_files = load_changed_files(repo_path=repo, base=base, head=head)
            repo_label = str(repo.resolve())

        try:
            cfg = load_config(path=config, repo_path=repo)
        except tomllib.TOMLDecodeError as exc:
            console.print(f"[red]Failed to parse config file:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        except ConfigError as exc:
            console.print(f"[red]Invalid config file:[/red] {exc}")
            raise typer.Exit(code=1) from exc

        changed_files = enrich_changed_files(changed_files, config=cfg)
        context_repo = str(repo.resolve())
        context = build_context(repo_path=context_repo, changed_files=changed_files, config=cfg)
        report = score_context(context, config=cfg)

        if output_format not in {"markdown", "json", "sarif", "annotations"}:
            console.print(
                "[red]Unsupported format. Use 'markdown', 'json', 'sarif', or 'annotations'.[/red]"
            )
            raise typer.Exit(code=2)

        if history_file is not None:
            prev = load_history(history_file)
            previous_score = prev[-1].score if prev else None
            trend = compute_trend(report.score, previous_score)
            report.metadata["risk_trend"] = trend
            commit = ""
            if not diff_file:
                try:
                    result = subprocess.run(
                        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True, timeout=10, check=True,
                    )
                    commit = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
                    if verbose:
                        console.print(
                            f"[yellow]Warning: could not determine commit hash: {exc}[/yellow]"
                        )
            append_history(history_file, report.score, report.risk_level, commit)

        if output_format == "markdown":
            rendered = render_markdown(report, config=cfg)
        elif output_format == "sarif":
            rendered = render_sarif(report)
        elif output_format == "annotations":
            rendered = render_annotations(report)
        else:
            rendered = json.dumps(report.to_dict(), indent=2, sort_keys=True)

        if output is not None:
            output.write_text(rendered, encoding="utf-8")
            typer.echo(f"Wrote report to {output}", err=True)

        typer.echo(rendered)

        if verbose:
            console.print(
                Panel.fit(
                    f"Repo: {repo_label}\n"
                    f"Files changed: {context.total_files_changed}\n"
                    f"Categories: {', '.join(sorted(context.categories_touched))}\n"
                    f"Components: {', '.join(sorted(context.components_touched))}",
                    title="MergeRadar Debug",
                )
            )

            table = Table("File", "Status", "Category", "Reason")
            for cf in changed_files:
                table.add_row(cf.path, cf.status, cf.category, cf.classification_reason or "")
            console.print(table)

        threshold = check if check is not None else _env_check()
        if threshold is not None and report.score >= threshold:
            raise typer.Exit(code=5)

    except DiffLoaderError as exc:
        console.print(f"[red]Failed to load diff:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _env_check() -> int | None:
    """Return the check threshold from the environment variable, if set."""
    val = os.environ.get("MERGERADAR_CHECK")
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


if __name__ == "__main__":
    app()
