from __future__ import annotations

from mergeradar.rules.base import CategoryChangedRule


class InfraConfigChangedRule(CategoryChangedRule):
    """Match changes classified as infrastructure or deployment configuration."""


class ApiSurfaceChangedRule(CategoryChangedRule):
    """Match changes classified as part of the public API surface."""


class ConfigChangedRule(CategoryChangedRule):
    """Match changes classified as application configuration."""


RULES = [
    InfraConfigChangedRule(
        id="infra.config_changed",
        title="Infrastructure or deployment config changed",
        score=2,
        category="infra",
        reason_prefix="Detected deployment or infrastructure changes in",
    ),
    ApiSurfaceChangedRule(
        id="api.surface_changed",
        title="Public API surface may have changed",
        score=2,
        category="api",
        reason_prefix="Detected API-related changes in",
    ),
    ConfigChangedRule(
        id="config.changed",
        title="Environment or app configuration changed",
        score=2,
        category="config",
        reason_prefix="Detected configuration changes in",
    ),
]
