from __future__ import annotations

import re

from mergeradar.models import RiskReport

_PATH_RE = re.compile(r"\b(?!\d+(?:\.\d+)+\b)([\w./:-]+\.\w+)\b")


def _sanitize_data(value: str) -> str:
    """Escape characters special to GitHub Actions workflow command data."""

    return value.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")


def _sanitize_property(value: str) -> str:
    """Escape characters special to GitHub Actions workflow command properties."""

    return _sanitize_data(value).replace(":", "%3A").replace(",", "%2C")


def _annotation_level(score: int) -> str:
    if score > 0:
        return "warning"
    return "notice"


def _extract_file_paths(reason: str) -> list[str]:
    return _PATH_RE.findall(reason)


def render_annotations(report: RiskReport) -> str:
    """Render triggered rules as GitHub Actions workflow command annotations.

    Each annotation is a single line like:
    ::warning file=path.py,line=1,title=MergeRadar (Rule)::message
    """

    lines: list[str] = []
    for rule in report.triggered_rules:
        level = _annotation_level(rule.score)
        files = rule.paths or _extract_file_paths(rule.reason)
        safe_reason = _sanitize_data(rule.reason)
        safe_title = _sanitize_property(rule.title)
        if files:
            for path in files:
                safe_path = _sanitize_property(path)
                lines.append(
                    f"::{level} file={safe_path},line=1,"
                    f"title=MergeRadar ({safe_title})::{safe_reason}"
                )
        else:
            lines.append(
                f"::{level} title=MergeRadar ({safe_title})::{safe_reason}"
            )

    return "\n".join(lines)
