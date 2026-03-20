# V0.1 CONTRACT

## INPUT

MergeRadar accepts a local git repo and one of these inputs:

### Supported modes

- Working tree diff
  - compare unstaged/staged changes to HEAD
- Commit range diff
  - example: main...feature-branch
- Explicit diff file
  - parse a unified diff from disk

### CLI contract

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

## Non-goal

v0.1 is not:

- an AI code reviewer
- a bug finder
- a security scanner
- a hosted SaaS
- a GitHub App

It is a change-risk summarizer.
