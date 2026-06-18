from __future__ import annotations

import re

from mergeradar.models import RiskReport

_PATH_RE = re.compile(r"\b([\w./-]+\.\w+)\b")


def _annotation_level(score: int) -> str:
    if score > 0:
        return "warning"
    return "notice"


def _extract_file_paths(reason: str) -> list[str]:
    return _PATH_RE.findall(reason)


def render_annotations(report: RiskReport) -> str:
    """Render triggered rules as GitHub Actions workflow command annotations.

    Each annotation is a single line like:
    ::warning title=MergeRadar::file=path.py,line=1::message
    """

    lines: list[str] = []
    for rule in report.triggered_rules:
        level = _annotation_level(rule.score)
        files = _extract_file_paths(rule.reason)
        if files:
            for path in files:
                lines.append(
                    f"::{level} title=MergeRadar ({rule.title})::"
                    f"file={path},line=1::{rule.reason}"
                )
        else:
            lines.append(
                f"::{level} title=MergeRadar ({rule.title})::{rule.reason}"
            )

    return "\n".join(lines)
