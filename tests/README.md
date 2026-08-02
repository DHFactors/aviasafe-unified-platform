# Testing

## 1. Structure

| Directory | Contents |
|-----------|----------|
| `backend/tests/` | Pytest unit/integration tests (backend) — **40 tests, all passing (RC-2)** |
| `e2e/` | End-to-end test scripts against the live API |

## 2. Unit/Integration Tests (`backend/tests/`)

Run from `backend/` (requires a working env — the suite uses mocks and does **not** need a live
Firestore):

```bash
cd backend
python -m pytest tests/ -q          # full suite
python -m pytest tests/test_risk_matrix.py -q   # single module
```

| Module | Tests | Covers |
|---|---|---|
| `test_health.py` | 3 | `/health`, `/live`, root endpoint |
| `test_metrics_service.py` | 7 | KPI calcs, risk distribution, hazard frequency, monthly trends, AI/org KPIs |
| `test_risk_assessment_lifecycle.py` | 14 | Submission auto-calculation (S×P), AI suggestion storage + aviation grounding, Safety Manager override (RBAC 403 checks for USER), full lifecycle, cross-tenant isolation |
| `test_risk_matrix.py` | 16 | Canonical `compute_risk_index`/`get_risk_level`/`classify_risk`/`risk_outcome` boundaries (5/9/15), empty-threshold robustness, custom thresholds, `get_thresholds` stored-config plumbing, hazard/report classification honours stored thresholds |

> **RC-2 note:** `test_risk_matrix.py` was added to lock the canonical risk scheme. Mocking note:
> tests monkeypatch the **consuming module** symbols (`app.services.hazard_service.get_thresholds`,
> `app.services.report_service.*`), not `app.firebase`, because the services import directly via
> `from ... import`.

## 3. Regression policy

- **All changes must keep `python -m pytest tests/ -q` green** (verified after RC-1 and RC-2).
- When behaviour changes, update the affected test in the same change.
- When new scoring/classification logic is introduced, add boundary tests (both sides of each
  threshold) in `test_risk_matrix.py`.

## 4. End-to-End Tests (`tests/e2e/`)

E2E scripts target the live API: `https://aviasafe-unified-platform.onrender.com`.

| Script | Lines | Purpose |
|--------|-------|---------|
| `e2e_test.py` | 403 | 10-scenario comprehensive test suite with per-scenario pass/fail and sub-check tracking |
| `e2e_test2.py` | 330 | Same 10 scenarios with simplified assertions and alternate-path resilience probing |
| `e2e_auth.py` | 58 | Auth helper — gets Firebase tokens for 4 test users, saves to `e2e_tokens.json` |
| `e2e_diag.py` | 113 | Diagnostic script — token decode + endpoint health check |
| `e2e_route_check.py` | 60 | OpenAPI spec route explorer — lists VSR, MOR, verification, diversion paths |
| `e2e_setup_claims.py` | 24 | One-shot claims setup via `/api/v1/admin/setup-claims` |
| `test_dash.py` | 23 | Quick dashboard test with Buddha Air tenant credentials |

### Running E2E

```bash
# Step 1: obtain tokens (fills tests/e2e/e2e_tokens.json)
python tests/e2e/e2e_auth.py

# Step 2: run suites
python tests/e2e/e2e_test.py
python tests/e2e/e2e_test2.py
python tests/e2e/e2e_diag.py
```

**Credentials:** E2E accounts use the env-driven seed/provisioning password
(`DEFAULT_SEED_PASSWORD` / `DEFAULT_PROVISION_PASSWORD`). Never hardcode or document passwords.

> `tests/e2e/e2e_tokens.json` is a runtime artifact (cached tokens) — do not commit.

## 5. Manual QA / UAT

See [docs/UAT_READINESS.md](../docs/UAT_READINESS.md) for the UAT scenario set (airline and CAAN
walkthroughs) and the current readiness note.

## 6. Known test gaps

- No CI workflow runs the suite automatically (see TD-8 in
  [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md)).
- No dedicated staging Firestore project for E2E; E2E runs against the shared live project.
