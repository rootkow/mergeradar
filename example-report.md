# MergeRadar Report

## Risk Level
**High** (score: 7)

## Summary
This change touches authentication-related code, deployment configuration, and a database migration. The combination increases the likelihood of rollout issues or user-facing auth regressions.

## Triggered Risk Signals
- **[+3] Database migration changed**
  - Detected changes under `alembic/versions/`
- **[+3] Auth-sensitive code changed**
  - Detected changes under `app/auth/` and `app/middleware/`
- **[+2] Deployment/config changed**
  - Detected changes in `.github/workflows/deploy.yml`
- **[+2] No tests changed for risky areas**
  - No matching test file changes were found

## Missing Evidence
- No tests were updated for auth/migration-related changes
- No documentation changes were detected
- No explicit rollback notes were provided

## Recommended Checks
- Validate the migration on a staging dataset
- Verify login, token refresh, and permission-protected endpoints
- Confirm deployment environment variables remain compatible
- Add or run targeted tests covering auth middleware and migration behavior

## Changed Files
### Application Code
- `app/auth/service.py`
- `app/middleware/session.py`

### Database
- `alembic/versions/20260320_add_user_status.py`

### Infrastructure
- `.github/workflows/deploy.yml`