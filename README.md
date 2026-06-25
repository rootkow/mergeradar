# MergeRadar

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Deterministic blast-radius and risk analysis for pull requests.

MergeRadar analyzes a Git diff or a saved unified diff and produces a Markdown or JSON report
describing which areas changed, what risk signals were triggered, and what should be checked before
merge or deployment.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Requires Python 3.11+ and Git (for live repos).

## Quick Start

```bash
mergeradar analyze                                       # diff working tree vs HEAD
mergeradar analyze --base main                           # diff against base branch
mergeradar analyze --diff-file samples/auth-change.diff  # analyze saved diff
mergeradar analyze --format json --check 6               # CI gate with score threshold
mergeradar analyze --format annotations                  # GitHub Actions inline feedback
```

See `mergeradar analyze --help` for all options.

## How It Works

1. Load changed files from diff
2. Classify each path (app, auth, API, DB, deps, infra, config, tests, docs)
3. Evaluate deterministic risk/stabilizer rules
4. Render score, gaps, and recommendations

| Score | Risk level |
| --- | --- |
| 0-2 | Low |
| 3-5 | Medium |
| 6+ | High |

## Current Rules

| Signal | Score |
| --- | ---: |
| Database migration changed | +3 |
| Auth-sensitive code changed | +3 |
| Infrastructure/deployment config changed | +2 |
| Public API surface changed | +2 |
| Environment/app config changed | +2 |
| Dependencies changed | +2 |
| No tests changed for risky areas | +2 |
| No docs changed for risky areas | +1 |
| Large diff threshold exceeded | +1 |
| Multiple top-level components changed | +2 |
| Cross-dependencies between changed files | +2 |
| Wide blast radius from internal imports | +1 |
| Docs-only change | -2 |
| Tests-only change | -1 |
| Lockfile-only change | -3 |

## Configuration

Create `.mergeradar.toml` to add custom keywords, override rule scores,
disable rules, or define custom category-based rules:

```toml
[keywords]
infra = ["kustomize", "argocd"]

[rules."db.migration_changed"]
enabled = false

[custom_rules]
"custom.secret_scanner" = { title = "Secret scanner changed", score = 3, category = "infra", reason = "Secret scanner configuration changed in" }
```

See `--verbose` output for rule IDs. Run `mergeradar analyze --help` for all
config options.

## Development

```bash
pytest
ruff check src/ tests/
```
