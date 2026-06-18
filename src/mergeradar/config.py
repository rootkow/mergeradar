from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RuleOverride:
    enabled: bool = True
    score: int | None = None


@dataclass(slots=True)
class MergeRadarConfig:
    keywords: dict[str, list[str]] = field(default_factory=dict)
    rules: dict[str, RuleOverride] = field(default_factory=dict)


class ConfigError(ValueError):
    """Raised when MergeRadar configuration is invalid."""


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
        for rule_id, rule_data in rules_raw.items():
            rule_id = str(rule_id)
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

    return MergeRadarConfig(keywords=keywords, rules=rules)
