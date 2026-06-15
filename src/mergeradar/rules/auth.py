from __future__ import annotations

from mergeradar.rules.base import CategoryChangedRule


class AuthPathTouchedRule(CategoryChangedRule):
    """Match changes classified as authentication or authorization code."""


RULE = AuthPathTouchedRule(
    id="auth.path_touched",
    title="Auth-sensitive code changed",
    score=3,
    category="auth",
    reason_prefix="Detected auth-sensitive code changes in",
)
