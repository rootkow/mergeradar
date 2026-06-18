from __future__ import annotations

from dataclasses import replace

from mergeradar.config import MergeRadarConfig
from mergeradar.rules.auth import RULE as AUTH_RULE
from mergeradar.rules.base import Rule
from mergeradar.rules.db import RULE as DB_RULE
from mergeradar.rules.deps import RULE as DEPS_RULE
from mergeradar.rules.evidence import RULES as EVIDENCE_RULES
from mergeradar.rules.infra import RULES as INFRA_RULES
from mergeradar.rules.scope import RULES as SCOPE_RULES


def get_rules(config: MergeRadarConfig | None = None) -> list[Rule]:
    """Return all analysis rules in evaluation order, with optional config overrides."""

    rules: list[Rule] = [DB_RULE, AUTH_RULE, DEPS_RULE, *INFRA_RULES, *EVIDENCE_RULES, *SCOPE_RULES]
    if config is None:
        return rules

    result: list[Rule] = []
    for rule in rules:
        override = config.rules.get(rule.id)
        if override is not None and not override.enabled:
            continue
        if override is not None and override.score is not None:
            result.append(replace(rule, score=override.score))
        else:
            result.append(rule)
    return result
