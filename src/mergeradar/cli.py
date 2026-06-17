from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mergeradar.analysis.classifier import enrich_changed_files
from mergeradar.analysis.context_builder import build_context
from mergeradar.analysis.scorer import score_context
from mergeradar.git.diff_loader import (
    DiffLoaderError,
    load_changed_files,
    load_changed_files_from_diff_file,
)
from mergeradar.git.repo_inspector import is_git_repo
from mergeradar.renderers.markdown import render_markdown

app = typer.Typer(help="Blast-radius and risk analysis for pull requests.")
console = Console()


@app.callback()
def main() -> None:
    """Define the MergeRadar command group."""


@app.command()
def analyze(
    repo: Annotated[Path, typer.Option("--repo", help="Path to the local git repository.")] = Path("."),
    base: Annotated[str | None, typer.Option("--base", help="Base ref to diff from.")] = None,
    head: Annotated[str | None, typer.Option("--head", help="Head ref to diff to.")] = None,
    diff_file: Annotated[Path | None, typer.Option("--diff-file", help="Path to a saved unified diff file.")] = None,
    output: Annotated[Path | None, typer.Option("--output", help="Optional file path to write the report.")] = None,
    output_format: Annotated[str, typer.Option("--format", help="Output format: markdown or json.")] = "markdown",
    check: Annotated[int | None, typer.Option("--check", help="Exit non-zero if risk score meets or exceeds this threshold.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Print extra debugging context.")] = False,
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

        changed_files = enrich_changed_files(changed_files)
        context = build_context(repo_path=repo_label, changed_files=changed_files)
        report = score_context(context)

        if output_format not in {"markdown", "json"}:
            console.print("[red]Unsupported format. Use 'markdown' or 'json'.[/red]")
            raise typer.Exit(code=2)

        rendered = (
            render_markdown(report)
            if output_format == "markdown"
            else json.dumps(report.to_dict(), indent=2, sort_keys=True)
        )

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
            raise typer.Exit(code=1)

    except DiffLoaderError as exc:
        console.print(f"[red]Failed to load diff:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _env_check() -> int | None:
    """Return the check threshold from the environment variable, if set."""
    val = os.environ.get("MERGEDARAR_CHECK")
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


if __name__ == "__main__":
    app()
