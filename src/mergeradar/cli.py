from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from mergeradar.analysis.classifier import enrich_changed_files
from mergeradar.analysis.context_builder import build_context
from mergeradar.analysis.scorer import score_context
from mergeradar.git.diff_loader import (
    DiffLoaderError,
    load_changed_files,
    load_changed_files_from_diff_file,
)
from mergeradar.git.repo_inspector import is_git_repo
from mergeradar.renderers.json import render_json
from mergeradar.renderers.markdown import render_markdown

app = typer.Typer(help="Blast-radius and risk analysis for pull requests.")
console = Console()


@app.callback()
def main() -> None:
    """MergeRadar CLI."""


@app.command()
def analyze(
    repo: Path = typer.Option(Path("."), "--repo", help="Path to the local git repository."),
    base: str | None = typer.Option(None, "--base", help="Base ref to diff from."),
    head: str | None = typer.Option(None, "--head", help="Head ref to diff to."),
    diff_file: Path | None = typer.Option(None, "--diff-file", help="Path to a saved unified diff file."),
    output: Path | None = typer.Option(None, "--output", help="Optional file path to write the report."),
    output_format: str = typer.Option("markdown", "--format", help="Output format: markdown or json."),
    verbose: bool = typer.Option(False, "--verbose", help="Print extra debugging context."),
) -> None:
    """Analyze a local git diff or a saved diff file."""

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

        rendered = render_markdown(report) if output_format == "markdown" else render_json(report)

        if output is not None:
            output.write_text(rendered, encoding="utf-8")
            console.print(f"[green]Wrote report to {output}[/green]")

        console.print(rendered)

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
    except DiffLoaderError as exc:
        console.print(f"[red]Failed to load diff:[/red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
