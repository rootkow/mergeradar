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

Analyze staged and unstaged changes in the current repository against `HEAD`:

```bash
mergeradar analyze
```

Analyze changes in another local repository:

```bash
mergeradar analyze --repo ../another-project
```

Analyze the changes introduced since a branch diverged from `main`:

```bash
mergeradar analyze --base main
```

Compare two explicit refs:

```bash
mergeradar analyze --base main --head feature/my-change
```

Analyze a saved unified diff:

```bash
mergeradar analyze --diff-file samples/auth-change.diff
```

Write a Markdown report to disk:

```bash
mergeradar analyze --output report.md
```

Write a structured JSON report:

```bash
mergeradar analyze --format json --output report.json
```

Add per-file classification details to the terminal output:

```bash
mergeradar analyze --verbose
```

Use the report as a CI gate — exit non-zero whenever the risk score meets or
exceeds a threshold:

```bash
mergeradar analyze --check 6
```

The threshold can also be set via the `MERGEDARAR_CHECK` environment variable.
The CLI flag takes precedence when both are set.

## Comparison Behavior

When no refs are supplied, MergeRadar runs the equivalent of `git diff HEAD`,
which includes staged and unstaged tracked changes but not untracked files.

Ref comparisons use Git's three-dot syntax:

| Options | Comparison |
| --- | --- |
| no `--base` or `--head` | `HEAD` versus the current working tree |
| `--base BASE` | `BASE...HEAD` |
| `--base BASE --head HEAD` | `BASE...HEAD` |

`--diff-file` reads the supplied unified diff instead of inspecting a
repository. Reports are always printed to the terminal; `--output` writes the
same report to a file as well.

## How Analysis Works

MergeRadar:

1. Loads changed file paths, statuses, additions, and deletions.
2. Classifies each path as application code, authentication, API, database,
   infrastructure, configuration, tests, documentation, or unknown.
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

Path classification is heuristic and case-insensitive. Rules inspect filenames,
extensions, and path segments; they do not parse source code.

## Sample Output

Running:

```bash
mergeradar analyze --diff-file samples/auth-change.diff
```

produces a report beginning with:

```markdown
# MergeRadar Report

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

Install the development dependencies as shown above, then run the test suite:

```bash
pytest
```

For a quick end-to-end CLI smoke test, analyze the included auth-change sample:

```bash
python -m mergeradar analyze --diff-file samples/auth-change.diff --format json
```

The test suite covers CLI output, diff loading, path classification, and
representative scoring behavior. Sample diffs are available in `samples/` for
manual CLI checks. Ruff is configured in `pyproject.toml` for formatting and
linting when working on code changes.

## Limitations

- Analysis is path-heuristic based, not AST-aware.
- Unified diff parsing is intentionally simple.
- Untracked files are not included when analyzing a local working tree.
- Recommendations are deterministic and generic rather than repository-specific.
- Risk scoring thresholds are configurable via `--check`; classification keywords are not yet user-configurable.

## Roadmap

### v0.2

- GitHub Action
- pull request comment mode
- CODEOWNERS awareness
- custom configuration file

### v0.3

- optional LLM-generated narrative summaries layered on deterministic signals
- richer ownership and runbook checks
- repository-specific rule tuning
