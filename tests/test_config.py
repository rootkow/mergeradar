import tomllib
from pathlib import Path

import pytest

from mergeradar.config import ConfigError, _parse_config, load_config


def test_load_config_returns_none_when_no_file(tmp_path: Path) -> None:
    cfg = load_config(repo_path=tmp_path)
    assert cfg is None


def test_load_config_finds_dot_file_in_repo(tmp_path: Path) -> None:
    config_file = tmp_path / ".mergeradar.toml"
    config_file.write_text('[keywords]\ninfra = ["kustomize"]\n')
    cfg = load_config(repo_path=tmp_path)
    assert cfg is not None
    assert cfg.keywords == {"infra": ["kustomize"]}


def test_load_config_explicit_path_overrides_repo(tmp_path: Path) -> None:
    repo_file = tmp_path / ".mergeradar.toml"
    repo_file.write_text('[keywords]\ninfra = ["from-repo"]\n')
    explicit = tmp_path / "custom.toml"
    explicit.write_text('[keywords]\ninfra = ["from-explicit"]\n')
    cfg = load_config(path=explicit, repo_path=tmp_path)
    assert cfg is not None
    assert cfg.keywords == {"infra": ["from-explicit"]}


def test_load_config_missing_explicit_path_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        load_config(path=tmp_path / "missing.toml", repo_path=tmp_path)


def test_invalid_toml_raises(tmp_path: Path) -> None:
    config_file = tmp_path / ".mergeradar.toml"
    config_file.write_text("{{invalid toml")
    with pytest.raises(tomllib.TOMLDecodeError):
        load_config(repo_path=tmp_path)


def test_parse_keywords() -> None:
    cfg = _parse_config({"keywords": {"auth": ["sso", "casbin"]}})
    assert cfg.keywords == {"auth": ["sso", "casbin"]}
    assert cfg.risky_categories == {"database", "auth", "infra", "config", "api", "deps"}


def test_parse_keywords_skips_non_dict() -> None:
    cfg = _parse_config({"keywords": "invalid"})
    assert cfg.keywords == {}


def test_parse_rule_disabled() -> None:
    cfg = _parse_config({"rules": {"db.migration_changed": {"enabled": False}}})
    assert cfg.rule_overrides["db.migration_changed"].enabled is False
    assert cfg.rule_overrides["db.migration_changed"].score is None


def test_parse_rule_score_override() -> None:
    cfg = _parse_config({"rules": {"db.migration_changed": {"score": 5}}})
    assert cfg.rule_overrides["db.migration_changed"].enabled is True
    assert cfg.rule_overrides["db.migration_changed"].score == 5


def test_parse_rule_rejects_non_integer_score() -> None:
    with pytest.raises(ConfigError, match="score must be an integer"):
        _parse_config({"rules": {"db.migration_changed": {"score": "high"}}})


def test_parse_rule_rejects_non_boolean_enabled() -> None:
    with pytest.raises(ConfigError, match="enabled must be true or false"):
        _parse_config({"rules": {"db.migration_changed": {"enabled": "no"}}})


def test_parse_rule_both() -> None:
    cfg = _parse_config({"rules": {"stability.lockfile_only": {"enabled": False, "score": -1}}})
    assert cfg.rule_overrides["stability.lockfile_only"].enabled is False
    assert cfg.rule_overrides["stability.lockfile_only"].score == -1


def test_parse_rules_skips_non_dict() -> None:
    cfg = _parse_config({"rules": "invalid"})
    assert cfg.rule_overrides == {}


def test_parse_risky_categories_override() -> None:
    cfg = _parse_config({"risky_categories": ["auth", "infra"]})
    assert cfg.risky_categories == {"auth", "infra"}


def test_parse_custom_rule_requires_reason() -> None:
    with pytest.raises(ConfigError, match="reason must be a string"):
        _parse_config(
            {
                "custom_rules": {
                    "custom.secret_scanner": {
                        "title": "Secret scanner changed",
                        "score": 3,
                        "category": "infra",
                    }
                }
            }
        )


def test_parse_custom_rule_with_reason() -> None:
    cfg = _parse_config(
        {
            "custom_rules": {
                "custom.secret_scanner": {
                    "title": "Secret scanner changed",
                    "score": 3,
                    "category": "infra",
                    "reason": "Secret scanner configuration changed in",
                }
            }
        }
    )

    assert len(cfg.custom_rules) == 1
    assert cfg.custom_rules[0].reason == "Secret scanner configuration changed in"
