# MergeRadar

**Deterministic blast-radius and risk analysis for pull requests.**

MergeRadar analyzes a local Git diff or a saved unified diff and produces a
Markdown or JSON report describing:

- which areas of the codebase changed
- which risk signals were triggered
- what supporting evidence is missing
- what should be checked before merge or deployment

MergeRadar is intentionally rule-based. Its output is inspectable and
repeatable across local reviews.

## Requirements

- Python 3.11 or newer
- Git, when analyzing a local repository

## Install

Clone the repository, create a virtual environment, and install MergeRadar with
its development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Confirm that the CLI is available:

```bash
mergeradar --help
```

You can also run the CLI without the installed console script:

```bash
python -m mergeradar --help
```

## Quick Start

```bash
# Compare current working tree against HEAD
mergeradar analyze

# Compare against a base branch (uses BASE...HEAD)
mergeradar analyze --base main

# Analyze a saved unified diff instead of a live repo
mergeradar analyze --diff-file samples/auth-change.diff

# Output as JSON and exit non-zero if score >= 6 (CI gate)
mergeradar analyze --format json --output report.json --check 6
```

The `--check` threshold can also be set via the `MERGEDARAR_CHECK` environment
variable. The CLI flag takes precedence.

Run `mergeradar analyze --help` for all options including `--repo`, `--head`,
`--verbose`, and `--format markdown` (the default).

## How Analysis Works

MergeRadar:

1. Loads changed file paths, statuses, additions, and deletions.
2. Classifies each path as application code, authentication, API, database,
   dependencies, infrastructure, configuration, tests, documentation, or unknown.
3. Builds context about the categories, top-level components, and total churn.
4. Evaluates deterministic risk and stabilizer rules.
5. Renders the resulting score, evidence gaps, recommendations, and changed
   files as Markdown or JSON.

Risk levels are derived from the final score:

| Score | Risk level |
| --- | --- |
| 0-2 | Low |
| 3-5 | Medium |
| 6 or higher | High |

Negative stabilizer scores cannot reduce the final score below zero.

## Current Rules

| Signal | Score | Trigger |
| --- | ---: | --- |
| Database migration changed | +3 | A migration, Alembic, or schema path changed |
| Auth-sensitive code changed | +3 | Auth, session, permission, OAuth, JWT, RBAC, or login code changed |
| Infrastructure or deployment config changed | +2 | Deployment, Docker, Terraform, Helm, Kubernetes, or workflow paths changed |
| Public API surface may have changed | +2 | API, route, endpoint, handler, OpenAPI, or Swagger code changed |
| Environment or app configuration changed | +2 | A recognized configuration file or path changed |
| Dependencies changed | +2 | A dependency or package manifest (e.g. `requirements.txt`, `package.json`, `Cargo.toml`) changed |
| No tests changed for risky areas | +2 | A risky category changed without a test-file change |
| No docs changed for risky areas | +1 | A risky category changed without a documentation change |
| Large diff size threshold exceeded | +1 | At least 400 changed lines or 15 changed files |
| Multiple top-level components changed | +2 | At least three top-level paths changed |
| Docs-only change | -2 | Every changed file is documentation |
| Tests-only change | -1 | Every changed file is a test |
| Lockfile-only change | -3 | Every changed file is a dependency lockfile (e.g. `package-lock.json`, `poetry.lock`) |

Path classification is heuristic and case-insensitive. Rules inspect filenames,
extensions, and path segments; they do not parse source code.

## Configuration

Create a `.mergeradar.toml` file in your repository root (or pass `--config`
with a custom path) to customize keyword matching and rule behavior.

### Custom keywords

```toml
[keywords]
# Supported categories: auth, api, database, tests, infra, config, deps.
infra = ["kustomize", "argocd"]
database = ["sequelize", "prisma"]
```

Keywords are matched case-insensitively against path segments and filename
tokens. A keyword containing a dot is compared against the full filename; a
keyword containing a slash is matched as a path prefix.

### Rule overrides

```toml
[rules."db.migration_changed"]
enabled = false

[rules."stability.lockfile_only"]
score = -1
```

Rules can be disabled entirely or have their score overridden. Run
`mergeradar analyze` with `--verbose` to see the rule IDs for each triggered
signal.

## Sample Output

Running `mergeradar analyze --diff-file samples/auth-change.diff` produces a
report that starts with:

```markdown
## Risk Level
**High** (score: 8)

## Summary
This change touches auth, infra and triggered the following main signals:
auth-sensitive code changed, infrastructure or deployment config changed,
no tests changed for risky areas.

## Triggered Risk Signals
- **[+3] Auth-sensitive code changed**
- **[+2] Infrastructure or deployment config changed**
- **[+2] No tests changed for risky areas**
- **[+1] No docs changed for risky areas**
```

The full report also includes reasons for each signal, missing evidence,
recommended checks, and changed files grouped by category.

## Development

```bash
pytest                              # run the test suite
ruff check src/ tests/              # lint
python -m mergeradar --help         # CLI smoke test
```

Sample diffs for manual testing are in the `samples/` directory.

## Roadmap

- **SARIF output** — `--format sarif` for GitHub Advanced Security integration.
- **Dependency walking** — Parse imports to better measure the blast radius.
- **PR annotations** — Post inline comments on changed lines for triggered rules.
- **Custom rules DSL** — Define rules in YAML without Python.
- **Historical scoring** — Track scores across commits to detect risk creep.
