# Tests

## Structure

| Directory | Contents |
|-----------|----------|
| `backend/tests/` | Pytest unit/integration tests (backend) |
| `e2e/` | End-to-end test scripts against the live API |

## E2E Tests (`e2e/`)

All E2E scripts target `https://aviasafe-unified-platform.onrender.com`.

| Script | Lines | Purpose |
|--------|-------|---------|
| `e2e_test.py` | 403 | 10-scenario comprehensive test suite with per-scenario pass/fail and sub-check tracking |
| `e2e_test2.py` | 330 | Same 10 scenarios with simplified assertions and alternate-path resilience probing |
| `e2e_auth.py` | 58 | Auth helper — gets Firebase tokens for 4 test users, saves to `e2e_tokens.json` |
| `e2e_diag.py` | 113 | Diagnostic script — token decode + endpoint health check |
| `e2e_route_check.py` | 60 | OpenAPI spec route explorer — lists VSR, MOR, verification, diversion paths |
| `e2e_setup_claims.py` | 24 | One-shot claims setup via `/api/v1/admin/setup-claims` |
| `test_dash.py` | 23 | Quick dashboard test with Buddha Air tenant credentials |

## Running

```bash
# Unit/integration tests (requires local backend)
pytest backend/tests/

# E2E tests (requires live API + valid Firebase credentials)
python tests/e2e/e2e_test.py
python tests/e2e/e2e_test2.py
python tests/e2e/e2e_diag.py
```
