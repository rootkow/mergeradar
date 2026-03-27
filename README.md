# MergeRadar

**Blast-radius and risk analysis for pull requests.**

MergeRadar analyzes a local git diff or a saved unified diff file and produces a
markdown or JSON report describing:

- what areas of the codebase were touched
- which risk signals were triggered
- what evidence is missing
- what should be checked before merge or deploy

## Why this exists

Most pull request tools are built to help reviewers comment on code changes.
MergeRadar is built to answer a different question:

> What could this change affect, and what should we verify before it ships?

The first version is intentionally deterministic and rule-based. That keeps the
output easier to inspect, easier to test, and easier to extend as the rules improve.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Usage

Analyze the current working tree against `HEAD`:

```bash
mergeradar analyze
```

Analyze a branch or commit range:

```bash
mergeradar analyze --base main --head HEAD
```

Analyze a saved diff file:

```bash
mergeradar analyze --diff-file samples/auth-change.diff
```

Write the report to disk:

```bash
mergeradar analyze --output report.md
```

Get JSON for automation:

```bash
mergeradar analyze --format json
```

## Sample output

```markdown
# MergeRadar Report

## Risk Level
**High** (score: 7)

## Summary
This change touches authentication-related code, deployment configuration, and a database migration.

## Triggered Risk Signals
- **[+3] Database migration changed**
- **[+3] Auth-sensitive code changed**
- **[+2] No tests changed for risky areas**
```

## Current rules

- database migration changed
- auth-sensitive path changed
- infra/deploy config changed
- public API path changed
- environment/config changed
- risky areas changed without tests
- risky areas changed without docs
- large diff threshold exceeded
- multiple top-level components touched
- docs-only or tests-only stabilizers

## Roadmap

### v0.2

- GitHub Action
- PR comment mode
- CODEOWNERS awareness
- custom config file

### v0.3

- optional LLM-generated narrative summary layered on deterministic signals
- richer ownership and runbook checks
- repository-specific rule tuning

## Limitations

- v0.1 is path-heuristic based, not AST-aware
- unified diff parsing is intentionally simple
- recommendations are deterministic and generic
