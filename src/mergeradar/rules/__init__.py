from __future__ import annotations

from mergeradar.rules.auth import RULE as AUTH_RULE
from mergeradar.rules.db import RULE as DB_RULE
from mergeradar.rules.evidence import RULES as EVIDENCE_RULES
from mergeradar.rules.infra import RULES as INFRA_RULES
from mergeradar.rules.scope import RULES as SCOPE_RULES


def get_rules():
    """Get all available rules.

    Returns:
        A list of all rules.
    """

    return [DB_RULE, AUTH_RULE, *INFRA_RULES, *EVIDENCE_RULES, *SCOPE_RULES]
