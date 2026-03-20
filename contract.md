# V0.1

## INPUT

MergeRadar accepts a local git repo and one of these inputs:

### Supported modes

- Working tree diff
  - compare unstaged/staged changes to HEAD
- Commit range diff
  - example: main...feature-branch
- Explicit diff file
  - parse a unified diff from disk

Examples:

```sh
mergeradar analyze
mergeradar analyze --base main --head HEAD
mergeradar analyze --diff-file sample.diff
```

### Required assumptions

- repo is local
- git is available
- diff is text-based
- only supported text files are analyzed in v0.1

### Supported file categories

We should classify, not deeply parse, these:

- app code: .py, .ts, .js, .go, .java
- config: .yaml, .yml, .json, .toml, .ini, .env*
- infra: Dockerfile, docker-compose*, helm/, k8s/, terraform/, .tf
- docs: .md, docs/
- tests: files/folders matching common test patterns
- db/migrations: migrations/, alembic/, sql/, files containing migration

## OUTPUT

### Primary output

A markdown report printed to stdout and optionally written to a file.
Example:

```sh
mergeradar analyze --base main --head HEAD --output report.md
```

### Report sections

- Overall risk level
  - low / medium / high
- Change summary
  - files changed
  - categories touched
  - likely affected areas
- Risk signals
  - list of triggered rules with explanations
- Missing evidence
  - tests not updated
  - no docs changes
  - no rollback note
  - etc.
- Recommended checks
  - concrete pre-merge or pre-deploy actions
- Changed files
  - grouped by category

### Machine-readable output

Also support:

```sh
mergeradar analyze --format json
```

JSON should include:

- risk_level
- score
- triggered_rules
- file_summary
- recommendations
- missing_evidence

## NON-GOAL

v0.1 is not:

- an AI code reviewer
- a bug finder
- a security scanner
- a hosted SaaS
- a GitHub App

## SCORING

Deterministic scoring (no LLM)

Risk levels:

- Low: score 0–2
- Medium: score 3–5
- High: score 6+

Initial rules:

- Each rule adds points.

High-signal rules:

- migration changed: +3
- auth/security-sensitive path changed: +3
- infra/deploy config changed: +2
- public API route/schema changed: +2
- env/config changed: +2

Evidence gap rules:

- risky code changed but no tests changed: +2
- risky code changed but no docs changed: +1
- large diff size threshold exceeded: +1
- multiple top-level components touched: +2

Stability helpers:

- only docs changed: -2
- only tests changed: -1

## RULES

Each rule must have:

- id
- name
- description
- severity_weight
- match(context) -> bool
- explanation(context) -> str

Example rule IDs:

- db.migration_changed
- auth.path_touched
- infra.config_changed
- evidence.no_tests_for_risky_change
- scope.multiple_components_changed

## REPOSITORY ANALYSIS

MergeRadar should build a small internal model from the diff (not building AST analysis in v0.1, path-based heuristics are enough):

Diff summary model

- changed files
- added/deleted lines
- renamed files
- top-level directories touched
- file categories touched

Repo context model

- test files present?
- docs folder present?
- migration folders present?
- infra folders present?
- ownership files present? (CODEOWNERS, runbooks maybe later)

## RECOMMENDATIONS

Recommendations should be deterministic and tied to triggered rules (no fluffy advice):

Examples:

- migration changed
  - "Validate migration on a staging snapshot before deploy."
- auth path changed
  - "Verify login, token/session validation, and permission boundaries."
- infra/config changed
  - "Confirm environment variable compatibility and deployment configuration."
- no tests for risky change
  - "Add or run targeted tests covering changed auth/config/migration paths."

## SUCCESS CRITERIA

MergeRadar v0.1 is done when:

- It runs against a local repo without crashing on normal diffs
- It classifies changed files into useful categories
- It computes a deterministic risk score
- It outputs a markdown report that feels credible
- It outputs JSON for automation
- It has at least 5-8 tests covering core rules and parsing
- It works on at least 2 real example repos or sample diffs

## CLI

Core command

```sh
mergeradar analyze
```

Options

```sh
mergeradar analyze --base main --head HEAD
mergeradar analyze --diff-file ./samples/auth-change.diff
mergeradar analyze --repo .
mergeradar analyze --output report.md
mergeradar analyze --format markdown
mergeradar analyze --format json
mergeradar analyze --verbose
```

Exit codes

- 0 success
- 1 runtime or parsing error
- 2 invalid arguments
- 3 not a git repo / diff unavailable

## BACKLOG

### v0.2

- GitHub Action
- PR comment output
- CODEOWNERS awareness
- better component inference

### v0.3

- LLM-generated narrative summary on top of deterministic rules
- custom rules config
- ignore patterns

### NEEDS TO BE PRIORITIZED

- GitHub Action
