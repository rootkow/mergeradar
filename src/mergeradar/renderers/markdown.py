from __future__ import annotations

from collections import defaultdict

from mergeradar.models import ChangedFile, RiskReport

# TODO: Configurationize this
CATEGORY_HEADINGS = {
    "app": "Application Code",
    "auth": "Authentication / Authorization",
    "api": "API Surface",
    "database": "Database",
    "infra": "Infrastructure",
    "config": "Configuration",
    "tests": "Tests",
    "docs": "Documentation",
    "unknown": "Other",
}


# TODO: Consider allowing the user to customize the Markdown output, e.g. by providing a template or
# configuration options for which sections to include, formatting styles, etc.
def render_markdown(report: RiskReport) -> str:
    """Render a RiskReport object as a Markdown string.

    Args:
        report: The RiskReport to render.

    Returns:
        A Markdown string representation of the report.
    """

    lines: list[str] = []
    lines.append("# MergeRadar Report")
    lines.append("")
    lines.append("## Risk Level")
    lines.append(f"**{report.risk_level}** (score: {report.score})")
    lines.append("")
    lines.append("## Summary")
    lines.append(report.summary)
    lines.append("")
    lines.append("## Triggered Risk Signals")

    if report.triggered_rules:
        for rule in report.triggered_rules:
            lines.append(f"- **[{rule.score:+d}] {rule.title}**")
            lines.append(f"  - {rule.reason}")
    else:
        lines.append("- No risk signals were triggered.")

    lines.append("")
    lines.append("## Missing Evidence")

    if report.missing_evidence:
        for item in report.missing_evidence:
            lines.append(f"- {item}")
    else:
        lines.append("- No obvious evidence gaps were detected.")

    lines.append("")
    lines.append("## Recommended Checks")

    for recommendation in report.recommendations:
        lines.append(f"- {recommendation}")

    lines.append("")
    lines.append("## Changed Files")
    grouped = _group_changed_files(report.changed_files)

    for category, files in grouped.items():
        lines.append(f"### {CATEGORY_HEADINGS.get(category, category.title())}")
        for changed_file in files:
            lines.append(
                f"- `{changed_file.path}` ({changed_file.status}, +{changed_file.additions}/-{changed_file.deletions})"
            )

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _group_changed_files(changed_files: list[ChangedFile]) -> dict[str, list[ChangedFile]]:
    """Group changed files by their category."""

    grouped: dict[str, list[ChangedFile]] = defaultdict(list)
    for changed_file in changed_files:
        grouped[changed_file.category].append(changed_file)

    return dict(grouped)
