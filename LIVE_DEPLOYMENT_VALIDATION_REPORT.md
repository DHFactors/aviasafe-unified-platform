# Live Deployment Validation Report — RC-5.5

**Release Validation Engineer — independent verification of the production deployment**
**Date:** 02 August 2026
**Target under test:** `https://aviasafe-unified-platform.onrender.com` (backend API) and
`https://gap-analysis-ssp.web.app` (frontend Hosting)
**Reference candidate:** RC-5 validated artifact (Docker image from working tree; commit `4e306ce` +
RC-1→RC-5 changes; OpenAPI 61 paths; admin endpoints `security: [{"HTTPBearer":[]}]`)
**Verdict:** **RC-5.5 FAILED – DEPLOYMENT VALIDATION FAILED**

> This phase is verification-only: no new features, no refactoring, no architecture changes, no
> documentation rewrite except recording validation results. All probes below are non-destructive.

---

## 1. Executive Summary

The operator-reported deployment was independently re-verified against the validated RC-5
candidate. **The live production deployment does NOT match the validated RC-5 candidate.**

- **Backend:** The live build is the **pre-RC-1 hardening build** (identical signature to committed
  HEAD `4e306ce`). Live OpenAPI shows admin POST endpoints with `security: null`; legacy
  `/check-data`, `/migrate-seed-data` and `/auth/debug-verify` endpoints are live; admin endpoints
  return **422 (body validation) rather than 403 (auth enforcement)**; the destructive
  `/seed-demo-data` and `/create-seed-users` endpoints are **alive and functional** (gated only by a
  publicly-known hardcoded setup secret). UAT-005 is therefore **NOT closed**.
- **Frontend:** Firebase Hosting is **not serving the application**. `gap-analysis-ssp.web.app`
  returns "Site Not Found" for every path; the hosting site has no channels/releases; the custom
  domains (`sms.` / `app.aviasafesystems.com`) have no DNS. The live backend's CORS allow-list
  trusts exactly `https://gap-analysis-ssp.web.app` — which is unreachable. The pilot application is
  effectively offline.
- **Root cause:** The RC-1→RC-5 security and functional fixes are **uncommitted** in the repository
  (git status shows `backend/app/routes/admin.py`, `config.py`, `auth.py`, and 40+ files modified on
  top of `4e306ce`). Any Render deploy that builds from the repository (committed history) therefore
  reproduces the vulnerable pre-RC-1 build. The deployment could not produce the validated candidate
  because the candidate was never committed.

**Correction required (operator/engineering):** (1) commit the RC-1→RC-5 working-tree changes;
(2) re-deploy the backend from the committed candidate; (3) redeploy the frontend to Firebase
Hosting; (4) re-verify per this report's checklist.

## 2. Deployment Verification

| Check | Expected (RC-5 candidate) | Live observed | Result |
|---|---|---|---|
| Service responding | 200 | 200 (`/health`) | ✅ |
| Application version | 1.0.0 | 1.0.0 | ✅ |
| `/live`, `/ready` | 200 | 200 / 200 (`firebase: connected`) | ✅ |
| OpenAPI path count | 61 | **64** (extra legacy paths) | ❌ |
| Admin POST `security` | `[{"HTTPBearer":[]}]` | **`null`** | ❌ |
| `/check-data`, `/migrate-seed-data`, `/auth/debug-verify` | absent | **present** | ❌ |
| No-token admin POST | 403 (auth first) | **422 (body first — auth not enforced)** | ❌ |
| `/seed-demo-data`, `/create-seed-users` | 404 (disabled) | **422 (alive)** | ❌ |
| Deployed source matches candidate | working tree | **committed HEAD `4e306ce`** | ❌ |

**Evidence:** live OpenAPI retrieved from `/openapi.json`; direct no-token probes; `git show
HEAD:backend/app/routes/admin.py` (hardcoded `SETUP_SECRET`, plain `!=` compare, `/check-data` +
`/migrate-seed-data` routes) and `git show HEAD:backend/app/routes/auth.py` (`/debug-verify`).

**Build/startup of the candidate (control):** the RC-5 candidate image was independently rebuilt and
booted during RC-5 (Docker build OK; admin endpoints 403; legacy paths 404; 46/46 tests). The live
behaviour diverges from that control on every security-relevant check, confirming the live build is
not the candidate.

## 3. Environment Verification

| Item | Status | Evidence / notes |
|---|---|---|
| Security headers | ✅ Present | HSTS, `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `X-Request-ID` all observed on live `/health` |
| CORS | ⚠️ | Live allows only `https://gap-analysis-ssp.web.app` — which is not serving (frontend offline); other origins rejected |
| Authentication endpoints | ✅ | `/api/v1/auth/verify` rejects invalid token (401); `/api/v1/auth/register` validates password (400) |
| Authentication hardening | ❌ | Legacy `/api/v1/auth/debug-verify` **live** (removed in RC-1) |
| Authorization (admin) | ❌ | Admin POST endpoints have no bearer auth (`security: null`; body validated first) |
| Secrets | ❌ | Deployed build contains hardcoded `SETUP_SECRET = "aviasafe-e2e-setup-2026"` (public, in git history) as the sole admin gate |
| Destructive endpoints | ❌ | `/seed-demo-data`, `/create-seed-users` alive; `DISABLE_DESTRUCTIVE_ENDPOINTS` gate absent from deployed build |
| Firestore config | ✅ | `/health` → `firebase: connected` |
| Rate limiting | ⚠️ | Global in-memory 60/min/IP middleware present in build; not stress-tested (non-destructive policy) |
| Frontend Hosting | ❌ | `gap-analysis-ssp.web.app` → "Site Not Found"; no hosting channels for site; `sms.`/`app.aviasafesystems.com` no DNS |

## 4. Smoke Test Results

All probes non-destructive (no authenticated writes; no destructive endpoint invoked).

| # | Scenario | Live result | Expected (candidate) | Status |
|---|---|---|---|---|
| 1 | Login (auth verify, invalid token) | 401 | 401 | ✅ |
| 2 | Logout | client-side (no server logout endpoint by design) | n/a | n/a |
| 3 | Dashboard API (no token) | 403 | 403 | ✅ |
| 4 | Dashboard frontend (`safety.html`) | **not reachable (Hosting down)** | 200 | ❌ |
| 5 | Survey page (`/survey/`) | **not reachable (Hosting down)** | 200 | ❌ |
| 6 | Hazard API (no token) | 403 | 403 | ✅ |
| 7 | Hazard pages | **not reachable (Hosting down)** | 200 | ❌ |
| 8 | VSR API (no token) | 403 | 403 | ✅ |
| 9 | VSR form (`/report/vsr.html`) | **not reachable (Hosting down)** | 200 | ❌ |
| 10 | MOR API (no token) | 403 | 403 | ✅ |
| 11 | MOR form (`/report/mor.html`) | **not reachable (Hosting down)** | 200 | ❌ |
| 12 | Reports API (no token) | 403 | 403 | ✅ |
| 13 | Admin API (no token) | **422 body-first (no auth)** | 403 | ❌ |
| 14 | Admin portal (`/admin/index.html`) | **not reachable (Hosting down)** | 200 | ❌ |
| 15 | Firestore writes | not exercised (requires credentials); rules validated in repo | — | ⚠️ |
| 16 | Tenant isolation | rules present in repo; not live-verified without tokens | — | ⚠️ |
| 17 | Protected endpoints | 403 on reports/dashboard/hazards/cans/flight-diversions/metrics | 403 | ✅ |
| 18 | Disabled endpoints (destructive) | **422 (alive)** — `/seed-demo-data`, `/create-seed-users` | 404 | ❌ |

Frontend rows (4,5,7,9,11,14) fail because Firebase Hosting is not serving the site — the pilot UI
is unavailable.

## 5. Security Validation

| RC-1 requirement | Verified live | Result |
|---|---|---|
| No legacy admin endpoints | `/check-data`, `/migrate-seed-data` present | ❌ |
| No `/debug-verify` | present | ❌ |
| No setup-secret bypass | Admin gated ONLY by hardcoded public `SETUP_SECRET`; no bearer token required | ❌ |
| Correct authorization | Admin POST `security: null`; no-token request reaches body validation | ❌ |
| Correct tenant isolation | Firestore rules in repo are tenant-isolated; not enforced by this build's API surface independently (no live token test) | ⚠️ |
| Security headers present | All present on live responses | ✅ |
| Destructive endpoints disabled | `/seed-demo-data`, `/create-seed-users` alive | ❌ |

**Conclusion: RC-1 security fixes are NOT active in production.**

## 6. Operational Validation

| Item | Status | Notes |
|---|---|---|
| Health endpoints | ✅ | `/health`, `/live`, `/ready` return 200; firebase connected |
| Error handling | ✅ | Structured JSON errors (`success/error/detail/errors/request_id`) for 400/401/403/422 |
| Logging | ⚠️ | loguru stdout (Render capture) + rotating JSON file in build; `X-Request-ID` present on responses; external log review not possible without Render access |
| Monitoring | ⚠️ | `/metrics` protected (403 no-token — correct); Prometheus-style counters are in-memory; no alerting |
| Audit logging | ❌ | No structured audit trail (documented limitation; unchanged) |
| Backup configuration | ❌ | No automated Firestore backups / PITR (operator action; unchanged) |
| Operational readiness | ❌ | Blocked by: un-hardened backend + offline frontend |

## 7. UAT-005 Closure Evidence

**UAT-005 is NOT closed.**

- Live OpenAPI: admin POST endpoints `security: null` (candidate: `[{"HTTPBearer":[]}]`).
- No-token admin POST → 422 (auth not enforced) instead of 403.
- Legacy `/check-data`, `/migrate-seed-data`, `/auth/debug-verify` live.
- Destructive `/seed-demo-data`, `/create-seed-users` alive (would run with the public hardcoded key).
- Deployed source = committed HEAD `4e306ce` (pre-RC-1). RC-1→RC-5 fixes are uncommitted
  (`git status` shows `admin.py`, `config.py`, `auth.py`, `+43` files modified).
- The validated RC-5 candidate image (built and boot-tested in RC-5) does not match the live build.

The UAT defect register has been updated: UAT-005 status **OPEN** with the RC-5.5 evidence recorded.

## 8. Remaining Risks

| # | Risk | Severity | Status |
|---|---|---|---|
| R-1 | Live backend un-hardened: admin endpoints unauth'd, hardcoded public `SETUP_SECRET`, destructive endpoints functional | **Critical** | Open — deployment failure |
| R-2 | Frontend not deployed: `gap-analysis-ssp.web.app` offline; custom domains no DNS | **Critical** | Open — deployment failure |
| R-3 | Deployed build ≠ validated candidate (release provenance broken) | **Critical** | Open — candidate never committed |
| R-4 | No automated Firestore backups / PITR | High | Open |
| R-5 | Public-create spam surface (no server-side App Check) | Medium-High | Open (TD-12) |
| R-6 | Self-registration accepts arbitrary `tenant_id` | Medium | Open (pilot decision) |
| R-7 | `/docs` exposed | Low | Open (UAT-009) |

## 9. Outstanding Technical Debt

Unchanged from `docs/KNOWN_LIMITATIONS.md` and `PROJECT_STATUS_REPORT_02AUG2026.md` (TD-6, TD-7,
TD-8, TD-10, TD-12, TD-15), plus: RC-1→RC-5 changes uncommitted (release-management debt); stale
`docs/OPERATIONS.md` provisioning example; Redis `ssl_cert_reqs=CERT_NONE`; `survey_submit`/
`dashboard` rate-limit definitions not attached.

## 10. Recommendation

**RC-5.5 FAILED – DEPLOYMENT VALIDATION FAILED.** The live production environment does not match the
validated RC-5 candidate, and UAT-005 (Critical) remains open in production.

Required corrective actions before re-validation:

1. **Commit the RC-1→RC-5 working-tree changes** so the release candidate is reproducible from
   committed history (this is the root cause of the failed deployment).
2. **Re-deploy the backend** from the committed candidate (Render service
   `aviasafe-unified-platform`, Docker path `backend/Dockerfile`); confirm env vars (`DEBUG=false`,
   `DISABLE_DESTRUCTIVE_ENDPOINTS=true`, `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`,
   `DEFAULT_SEED_PASSWORD`).
3. **Redeploy the frontend** to Firebase Hosting (`firebase deploy --only hosting` for
   `gap-analysis-ssp.web.app`) or publish a verified custom domain and update `ALLOWED_ORIGINS`.
4. **Re-run this validation:** live OpenAPI admin `security: [{"HTTPBearer":[]}]`; legacy paths 404;
   no-token admin → 403; destructive endpoints → 404; frontend pages 200; UAT-005 CLOSED.
5. Enable Firestore Backups/PITR before pilot users enter data.

The verdict is `RC-5.5 FAILED` until steps 1–4 are completed and re-verified. RC-6 must not begin.
