from __future__ import annotations

import json
from importlib.metadata import version as _pkg_version

from mergeradar.models import RiskReport, TriggeredRule

SARIF_SCHEMA: str = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
    "master/Schemata/sarif-schema-2.1.0.json"
)

try:
    __version__ = _pkg_version("mergeradar")
except Exception:
    __version__ = "0.0.0"


def _level(score: int) -> str:
    return "warning" if score > 0 else "note"


def _extract_paths(reason: str) -> list[str]:
    if ": " not in reason:
        return []
    after_colon = reason.split(": ", 1)[1]
    return [p.strip() for p in after_colon.split(", ") if p.strip()]


def _sarif_result(rule: TriggeredRule) -> dict:
    result: dict = {
        "ruleId": rule.id,
        "level": _level(rule.score),
        "message": {"text": rule.reason},
    }
    paths = _extract_paths(rule.reason)
    if paths:
        result["locations"] = [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": path},
                },
            }
            for path in paths
        ]
    return result


def render_sarif(report: RiskReport) -> str:
    results = [_sarif_result(rule) for rule in report.triggered_rules]

    sarif: dict = {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "MergeRadar",
                        "version": __version__,
                        "informationUri": "https://github.com/rootkow/mergeradar",
                    },
                },
                "results": results,
                "columnKind": "unicodeCodePoints",
                "properties": {
                    "riskScore": report.score,
                    "riskLevel": report.risk_level,
                },
            },
        ],
    }

    return json.dumps(sarif, indent=2)
