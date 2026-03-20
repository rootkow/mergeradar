from __future__ import annotations

from mergeradar.models import AnalysisContext, TriggeredRule
from mergeradar.rules.base import SimpleRule


class InfraConfigChangedRule(SimpleRule):
    """Rule that triggers when infrastructure or deployment configuration changes are detected."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not context.has_infra_changes:
            return None

        infra_paths = [f.path for f in context.changed_files if f.category == "infra"]
        reason = f"Detected deployment or infrastructure changes in: {', '.join(infra_paths[:3])}"
        return self.trigger(reason)


class ApiSurfaceChangedRule(SimpleRule):
    """Rule that triggers when changes to the public API surface are detected."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not context.has_api_changes:
            return None

        api_paths = [f.path for f in context.changed_files if f.category == "api"]
        reason = f"Detected API-related changes in: {', '.join(api_paths[:3])}"
        return self.trigger(reason)


class ConfigChangedRule(SimpleRule):
    """Rule that triggers when configuration changes are detected."""

    def evaluate(self, context: AnalysisContext) -> TriggeredRule | None:
        """Evaluate the rule against the given analysis context.

        Args:
            context: The analysis context.

        Returns:
            A TriggeredRule if the rule is triggered, otherwise None.
        """

        if not context.has_config_changes:
            return None

        config_paths = [f.path for f in context.changed_files if f.category == "config"]
        reason = f"Detected configuration changes in: {', '.join(config_paths[:3])}"
        return self.trigger(reason)


RULES = [
    InfraConfigChangedRule(
        id="infra.config_changed",
        title="Infrastructure or deployment config changed",
        score=2,
    ),
    ApiSurfaceChangedRule(
        id="api.surface_changed",
        title="Public API surface may have changed",
        score=2,
    ),
    ConfigChangedRule(
        id="config.changed",
        title="Environment or app configuration changed",
        score=2,
    ),
]
