from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mergeradar.exceptions import ConfigError


@dataclass(slots=True)
class RuleOverride:
    enabled: bool = True
    score: int | None = None


@dataclass(slots=True)
class CustomRuleDef:
    id: str
    title: str
    score: int
    category: str
    reason: str


@dataclass(slots=True)
class MergeRadarConfig:
    keywords: dict[str, list[str]] = field(default_factory=dict)
    rule_overrides: dict[str, RuleOverride] = field(default_factory=dict)
    risky_categories: set[str] = field(
        default_factory=lambda: {"database", "auth", "infra", "config", "api", "deps"}
    )
    category_headings: dict[str, str] = field(default_factory=dict)
    custom_rules: list[CustomRuleDef] = field(default_factory=list)


def load_config(path: Path | None = None, repo_path: Path = Path(".")) -> MergeRadarConfig | None:
    """Load config from --config path or .mergeradar.toml in repo root."""

    if path is not None and not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")

    search_paths: list[Path] = []
    if path is not None:
        search_paths.append(path)
    search_paths.append(repo_path / ".mergeradar.toml")

    for p in search_paths:
        if p.exists():
            with p.open("rb") as f:
                data = tomllib.load(f)
            return _parse_config(data)

    return None


def _parse_required_str_list(raw: object, key: str) -> set[str]:
    """Convert a required TOML list value to a set of strings."""

    if not isinstance(raw, list):
        raise ConfigError(f"'{key}' must be a list of strings.")
    return {str(item) for item in raw}


def _parse_str_dict(raw: object) -> dict[str, str]:
    """Convert a TOML table to a dict of strings. Returns empty dict for non-dict input."""

    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    return {}


def _parse_config(data: dict[str, Any]) -> MergeRadarConfig:
    keywords: dict[str, list[str]] = {}
    keywords_raw = data.get("keywords", {})
    if isinstance(keywords_raw, dict):
        for k, v in keywords_raw.items():
            if isinstance(v, list):
                keywords[str(k)] = [str(i) for i in v]

    rules: dict[str, RuleOverride] = {}
    rules_raw = data.get("rules", {})
    if isinstance(rules_raw, dict):
        for raw_rule_id, rule_data in rules_raw.items():
            rule_id = str(raw_rule_id)
            if isinstance(rule_data, dict):
                enabled = rule_data.get("enabled", True)
                score = rule_data.get("score")
                if not isinstance(enabled, bool):
                    raise ConfigError(f"Rule '{rule_id}' enabled must be true or false.")
                if score is not None and (not isinstance(score, int) or isinstance(score, bool)):
                    raise ConfigError(f"Rule '{rule_id}' score must be an integer.")
                rules[rule_id] = RuleOverride(
                    enabled=enabled,
                    score=score,
                )

    custom_rules: list[CustomRuleDef] = []
    custom_raw = data.get("custom_rules", {})
    if isinstance(custom_raw, dict):
        for raw_rule_id, rule_data in custom_raw.items():
            rule_id = str(raw_rule_id)
            if isinstance(rule_data, dict):
                title = rule_data.get("title")
                score = rule_data.get("score")
                category = rule_data.get("category")
                reason = rule_data.get("reason")
                if not isinstance(title, str):
                    raise ConfigError(f"Custom rule '{rule_id}' must have a string title.")
                if not isinstance(score, int) or isinstance(score, bool):
                    raise ConfigError(f"Custom rule '{rule_id}' score must be an integer.")
                if not isinstance(category, str):
                    raise ConfigError(f"Custom rule '{rule_id}' category must be a string.")
                if not isinstance(reason, str):
                    raise ConfigError(f"Custom rule '{rule_id}' reason must be a string.")
                custom_rules.append(
                    CustomRuleDef(
                        id=rule_id,
                        title=title,
                        score=score,
                        category=category,
                        reason=reason,
                    )
                )

    return MergeRadarConfig(
        keywords=keywords,
        rule_overrides=rules,
        risky_categories=(
            _parse_required_str_list(data["risky_categories"], "risky_categories")
            if "risky_categories" in data
            else {"database", "auth", "infra", "config", "api", "deps"}
        ),
        category_headings=_parse_str_dict(data.get("headings")),
        custom_rules=custom_rules,
    )
