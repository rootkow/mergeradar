from __future__ import annotations

import json

from mergeradar.models import RiskReport


def render_json(report: RiskReport) -> str:
    """Render a RiskReport object as a JSON string.

    Args:
        report: The RiskReport to render.

    Returns:
        A JSON string representation of the report.
    """

    # TODO: Optional configuration for pretty-printing, filtering fields, etc.
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)
