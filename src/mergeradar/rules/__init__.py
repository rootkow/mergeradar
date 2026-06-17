from __future__ import annotations

from mergeradar.rules.auth import RULE as AUTH_RULE
from mergeradar.rules.base import Rule
from mergeradar.rules.db import RULE as DB_RULE
from mergeradar.rules.deps import RULE as DEPS_RULE
from mergeradar.rules.evidence import RULES as EVIDENCE_RULES
from mergeradar.rules.infra import RULES as INFRA_RULES
from mergeradar.rules.scope import RULES as SCOPE_RULES


def get_rules() -> list[Rule]:
    """Return all analysis rules in evaluation order."""

    return [DB_RULE, AUTH_RULE, DEPS_RULE, *INFRA_RULES, *EVIDENCE_RULES, *SCOPE_RULES]
