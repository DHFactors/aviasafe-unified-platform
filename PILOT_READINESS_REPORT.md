# AviaSAFE Pilot Readiness Report — RC-5

**Release Engineer assessment for first operational pilot deployment**
**Date:** 02 August 2026
**Phase:** RC-5 — Operational Pilot Readiness
**Verdict:** READY FOR RC-6 – PRODUCTION READINESS REVIEW (conditional upon successful Render
deployment — see §12 Pending Operator Actions)

> Scope discipline: no new features, no architectural redesign, no unrelated refactoring. This
> report is operational-readiness work only. Three states are explicitly distinguished throughout:
> **Repository state (validated)**, **Local deployment validation (passed)**, and **Live production
> state (pending operator action)**.

---

## 1. Executive Summary

AviaSAFE is prepared for its first operational pilot. RC-5 completed six workstreams: deployment
verification, pilot environment validation, operational readiness, pilot airline onboarding review,
production monitoring assessment, and the release package.

The **deployable artifact is validated**: the Docker image builds from the working tree, boots,
serves all routes, enforces bearer authentication on protected **and** admin endpoints (403 before
body validation), contains no legacy debug/destructive paths, generates valid PDF reports, and
passes the full regression suite (**46/46**). This confirms the RC-5 candidate contains the UAT-005
authorization fix.

The **live production build is the pre-hardening build**: live OpenAPI shows admin POST endpoints
with `security: null`, and legacy `/check-data` and `/migrate-seed-data` paths remain live. The
Render re-deploy is an external operational dependency (operator credentials) and is recorded as a
Pending Operator Action. The pilot must not begin until it is completed.

Operational documentation is comprehensive (OPERATIONS, DEPLOYMENT, ADMIN_GUIDE, API,
KNOWN_LIMITATIONS, tenant-guide 01–03, onboarding reference). Gaps are documented in §4, §5, §8, §9.
The most consequential outstanding risks are the pending deployment (R-A), the absence of automated
Firestore backups (R-B), and the public-create spam surface without server-side App Check (R-C).

## 2. Deployment Verification

### 2.1 Repository state (validated)
- Working tree = commit `4e306ce` + RC-1→RC-5 changes (46 files modified). All fixes from RC-4
  (UAT-001/002/003/004/006/007/008) are present.
- No live secrets in code: grep for `aviasafe-e2e-setup-2026`, `AIzaSyFakeKey`, GitHub tokens, and
  private keys returns only historical references in the status report (retired values) and the
  `.env.example` placeholder. Real credentials exist only in `backend/.env` (local, placeholder key)
  and Render env (real).
- `python -m pytest tests/ -q` → **46 passed**.

### 2.2 Local deployment validation (passed)
- **Build:** `docker build -f backend/Dockerfile backend/` → success (1 minor warning: `CMD` should
  use JSON args; non-blocking). Python 3.11 image; reportlab 4.1.0 installed.
- **Startup:** container boots; uvicorn serves; app.main imports (153 routes registered).
- **Configuration validation:** all `Settings` fields resolve; `DISABLE_DESTRUCTIVE_ENDPOINTS=True`
  (default); `CROSS_TENANT_ROLES=['CAAN_SMD','SUPER_ADMIN']`; CORS allow-list resolves.
- **Environment validation:** `DEBUG=True` in local `.env` (must be `false` in production);
  `SETUP_SECRET`/`DEFAULT_PROVISION_PASSWORD`/`DEFAULT_SEED_PASSWORD` unset locally (documented in
  `.env.example`); local `FIREBASE_PRIVATE_KEY` is a placeholder (real key only on Render — live
  `/health` reports `firebase: connected`).
- **Smoke (local container):** `/health` 200, `/live` 200, `/ready` 200; `GET /api/v1/reports`
  (no token) → 403; `POST /api/v1/admin/setup-claims` (no token, empty body) → **403 Not
  authenticated (before body validation)**; OpenAPI shows all admin POST endpoints with
  `security: [{"HTTPBearer":[]}]`; legacy `/check-data` and `/migrate-seed-data` absent (404);
  `generate_report_pdf(...)` → `%PDF-1.4` (valid).

### 2.3 Live production state (pending operator action)
- `/health` → `{"status":"healthy","firebase":"connected"}`; `/live` 200; `/ready` 200.
- `POST /api/v1/auth/verify` with invalid token → 401. Protected surfaces (reports, dashboard,
  hazards, cans, flight-diversions, `/metrics`) → 403.
- **Admin POST endpoints have `security: null`** in live OpenAPI; legacy `/check-data` and
  `/migrate-seed-data` still live → **UAT-005 remains open**.
- `/docs` exposed (200); `/api/v1/surveys` → 404 (no backend survey route; survey is client-side
  Firestore).
- **Action required:** re-deploy the RC-5 candidate (see §12).

## 3. Smoke Test Results

| # | Check | Live (current build) | RC-5 candidate (local) | Result |
|---|-------|----------------------|------------------------|--------|
| 1 | `/health` | 200, firebase connected | 200 (firebase unavailable — placeholder local key) | PASS |
| 2 | `/live` | 200 | 200 | PASS |
| 3 | `/ready` | 200, ready | 200 | PASS |
| 4 | Auth invalid token | 401 | 401 | PASS |
| 5 | Protected surface no-token | 403 | 403 | PASS |
| 6 | Admin endpoint no-token | **422 (body first — auth NOT enforced)** | **403 (auth enforced)** | **FAIL on live / PASS on candidate** |
| 7 | Admin OpenAPI security | **null** | `HTTPBearer` | **FAIL on live / PASS on candidate** |
| 8 | Legacy `/check-data`, `/migrate-seed-data` | **present** | absent | **FAIL on live / PASS on candidate** |
| 9 | `/docs` exposure | exposed (200) | exposed (candidate, UAT-009 rec.) | Note |
| 10 | PDF report generation | n/a (reportlab absent on live) | valid `%PDF-1.4` | PASS on candidate |
| 11 | Regression suite | — | 46/46 passed | PASS |

Rows 6–8 are the UAT-005 discrepancy: the live build predates RC-1 hardening. All checks must be
re-run against the live environment after the operator deploys the RC-5 candidate (§12).

## 4. Operational Readiness

### 4.1 Required procedures — status

| Procedure | Status | Where / notes |
|---|---|---|
| System administration | ✅ Present | `docs/OPERATIONS.md`, `docs/ADMIN_GUIDE.md` |
| Tenant provisioning | ✅ Present | `/provision-airlines`, `scripts/provision-20-airlines.js`, ADMIN_GUIDE |
| User provisioning | ✅ Present | `/setup-claims`, `/create-seed-users`, seed scripts |
| Password reset | ✅ Present | Firebase Auth console / email reset (standard flow); documented in tenant-guide step 02 |
| Incident response | 🔶 Partial | OPERATIONS playbook line; no dedicated runbook / escalation matrix |
| Backup | 🔶 Documented, not enabled | OPERATIONS §5; **no automated backups / PITR configured** (operator action) |
| Recovery | ✅ Present | OPERATIONS §5 restore/re-seed steps; DEPLOYMENT rollback |
| Monitoring | ✅ Present | `/health`, `/live`, `/ready`, `/metrics`; request logs |
| Log review | 🔶 Partial | loguru stdout (Render capture) + rotating JSON file; no alerting/retention policy |
| Support escalation | 🔶 Partial | No named support contact / SLA documented |
| Deployment | ✅ Present | `docs/DEPLOYMENT.md` §3/§7 (release procedure) |
| Rollback | ✅ Present | DEPLOYMENT §3 (Render previous-deploy rollback), §5 (Hosting release history) |
| Release management | ✅ Present | Phase governance + `PROJECT_STATUS_REPORT` + RELEASE_NOTES_RC5 |

### 4.2 Documentation gaps found
1. `docs/OPERATIONS.md` §2.2 provisioning example is **stale**: shows `X-Setup-Key` header and a
   `password` body; the current code requires `setup_key` **in the JSON body** and reads the
   password from the `DEFAULT_PROVISION_PASSWORD` env var. Example must be corrected.
2. No explicit incident-response runbook (severity levels, call tree, comms).
3. No named support contact / escalation path (single-maintainer risk, R10).
4. No dedicated staging environment (staging shares production Firestore).

## 5. Monitoring Assessment

### 5.1 Capabilities verified

| Capability | Status | Evidence |
|---|---|---|
| Application logs | ✅ | loguru stdout + `logs/aviasafe.json` (100 MB rotation, 30-day retention); per-request structured logs with `request_id`, method, path, status, duration, user/tenant/role |
| Error logs | ✅ | `logger.error` on 5xx and unhandled exceptions; log level filtering |
| Audit logs | ❌ | **No structured audit trail** (e.g., who confirmed which risk assessment) — documented limitation |
| Health endpoints | ✅ | `/health`, `/live`, `/ready` (liveness/readiness for Render & Cloud Run) |
| Performance monitoring | 🔶 | `/metrics` (SUPER_ADMIN) exposes `request_duration_ms` histogram, `requests_total`, AI success rate, Firestore latency (p99) — all **in-memory** (lost on restart) |
| Failure alerts | ❌ | **No alerting configured** (no Prometheus scrape target, no email/webhook alerting) |
| Operational metrics | 🔶 | `requests_total`, AI counters, Firestore latency gauges (in-memory) |
| Security events | 🔶 | Request logs only; no SIEM / dedicated security event stream |

### 5.2 Missing monitoring capability
- Prometheus integration / metric scraping endpoint and external metric store.
- Alerting (error-rate, health, AI-failure, rate-limit-threshold, 5xx spikes).
- External/durable log retention (in-memory metrics and container files are ephemeral).
- Structured audit trail for regulatory actions (risk-assessment confirmations, tenant admin
  actions).
- Dashboards (Grafana / Firebase console) and on-call/rotation definition.

## 6. Backup & Recovery Assessment

- **Backups:** **No automated Firestore backups or PITR are enabled.** Firestore retains only the
  default snapshot set unless operator enables Cloud Backups/PITR. This is the highest-priority
  data-protection gap for the pilot.
- **Recovery:** documented procedure exists (OPERATIONS §5): restore most-recent backup to the
  project, or re-seed demo data; recreate Auth users via provisioning; re-verify rules/indexes.
  Auth user records are separate from Firestore (restore both).
- **Rollback:** Render keeps prior deploys (dashboard "Rollback"); env-driven config means a prior
  image restores a known-good state. Hosting rollback via "Release history". Rules rollback by
  re-deploying prior rules.
- **Recommendation (pilot gate):** enable Firestore Backups (and PITR) for `gap-analysis-ssp`
  before pilot users enter data.

## 7. Security Review

| Control | Status | Notes |
|---|---|---|
| Authentication (Firebase ID tokens, RS256) | ✅ | Backend verifies via Admin SDK; invalid token → 401 |
| Authorization / RBAC (4 roles) | ✅ | Claim-based; dependency guards; CROSS_TENANT_ROLES scoped; RC-4 fixes verified |
| Admin surface | ✅ in candidate / ❌ live | RC-5 candidate: SUPER_ADMIN Bearer + env setup key, fail-closed 503; **live build unauth'd until re-deploy (UAT-005)** |
| Tenant isolation (Firestore rules) | ✅ | Own-tenant reads/writes; CAAN cross-tenant read-only; immutable responses/reports; UAT-004 alignment present |
| App Check | 🔶 | Client-side reCAPTCHA v3 (key committed); **no server-side verification** (TD-12); rules contain no `request.app.check` attestation conditions despite SECURITY.md claim (doc gap) |
| Security headers | ✅ | Backend middleware (HSTS, nosniff, DENY, XSS, referrer, permissions-policy) + Hosting headers |
| Rate limiting | 🔶 | Global 60 req/min/IP in-memory; Redis-backed per-route on 3 routes; `survey_submit`/`dashboard` limits defined but not attached; Redis TLS `ssl_cert_reqs=CERT_NONE` |
| Secrets | ✅ | No live secrets in code (grep clean); env-driven; retired-secret strings remain only as historical text in the status report (minor) |
| Secrets in production env | 🔶 | Operator must set `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`, `DEFAULT_SEED_PASSWORD`; `DEBUG=false` |
| Registration | 🔶 | Self-registration allows **self-assigned `tenant_id`** (any tenant as AIRLINE_ADMIN) — pilot risk; recommend disabling self-registration or domain-validation during pilot |
| Documentation | 🔶 | SECURITY.md App Check claim vs rules; OPERATIONS provisioning example stale |

## 8. Known Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R-A | Live backend runs pre-hardening build (admin unauth'd) | Certain until re-deploy | Critical | Operator re-deploy (Pending Operator Action 1); verify before pilot |
| R-B | No automated backups / PITR | High (data loss on incident) | High | Enable Firestore Backups/PITR (pilot gate) |
| R-C | Public-create spam surface (VSR/responses) | Medium | Medium-High | Server-side App Check + attach `survey_submit` rate limit (TD-12) |
| R-D | Self-registration arbitrary `tenant_id` | Medium | Medium | Disable self-registration or validate during pilot |
| R-E | Survey non-charter-compliant | Certain | Medium | Tracked (TD-6); interim scores flagged |
| R-F | `/docs` exposed | Certain | Low | `docs_url=None` in production (UAT-009) |
| R-G | `DEBUG` misconfigured in prod | Low | Medium | Confirm `DEBUG=false` in Render env |
| R-H | Single maintainer / no support contact | Medium | Medium | Document escalation path; bus-factor mitigation |
| R-I | No CI/CD; deploy drift (TD-8) | Medium | Medium | Post-pilot: CI with pytest + single render.yaml |
| R-J | Index camelCase/snake_case drift (TD-10) | Medium | Medium | Reconcile indexes with actual queries |
| R-K | Redis TLS verification disabled | Medium | Low-Medium | Enable certificate verification |

## 9. Open Technical Debt

See `docs/KNOWN_LIMITATIONS.md` (authoritative) and `PROJECT_STATUS_REPORT_02AUG2026.md` §7.
Carried and new:

- **TD-6** Survey charter re-alignment (4 components / 12 elements) — highest-priority functional debt.
- **TD-7** `public/portal` mock code / fake-key remnants removal.
- **TD-8** No CI/CD; two `render.yaml`; service-name mismatch (`aviasafe-unified-platform` vs
  `aviasafe-api`).
- **TD-10** Firestore indexes camelCase vs snake_case drift (`firestore.indexes.json` vs
  `backend/firestore.indexes.json`; `backend/` copy unused).
- **TD-12** Server-side App Check enforcement; public-create spam control.
- **TD-15** `seed_metadata.seeded_at` stored as ISO string.
- **New** Self-registration `tenant_id` validation.
- **New** `docs/OPERATIONS.md` provisioning example outdated.
- **New** Redis `ssl_cert_reqs=CERT_NONE` (from TD-18).
- **New** `survey_submit` / `dashboard` rate-limit definitions never attached to routes.

## 10. Pilot Deployment Checklist

**Operator actions (blocking):**
- [ ] Trigger Render deployment of the RC-5 candidate (service `aviasafe-unified-platform`, Docker
      path `backend/Dockerfile`, `healthCheckPath: /live`).
- [ ] Set/confirm Render env: `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`, `DEFAULT_SEED_PASSWORD`,
      `DEBUG=false`, `DISABLE_DESTRUCTIVE_ENDPOINTS=true`, `ALLOWED_ORIGINS` (incl.
      `https://gap-analysis-ssp.web.app`), Firebase + Gemini + `REDIS_URL`.
- [ ] Verify live OpenAPI: admin POST `security: [{"HTTPBearer":[]}]`; `/check-data`,
      `/migrate-seed-data` absent.
- [ ] Run production smoke tests against live (health/live/ready; auth 401; protected 403; one VSR
      + one MOR; dashboard; risk-matrix; report generation with valid PDF).
- [ ] Confirm UAT-005 resolved; record deployment timestamp + deployed commit hash.
- [ ] Confirm production matches the validated repository.

**Recommended before pilot users (non-blocking but advised):**
- [ ] Enable Firestore Backups/PITR for `gap-analysis-ssp`.
- [ ] Decide self-registration policy (recommend disabling or email-domain validation).
- [ ] Correct the stale provisioning example in `docs/OPERATIONS.md`.
- [ ] Attach `survey_submit` rate limit (and document spam controls).
- [ ] Set `docs_url=None` (or restrict) in production; add `X-Request-ID` guidance to ops docs.
- [ ] Add Prometheus scraping + alerting (post-pilot acceptable).
- [ ] Establish a support/escalation contact for pilot airlines.

## 11. Go / No-Go Recommendation

**GO — READY FOR RC-6 – PRODUCTION READINESS REVIEW**, conditional upon successful Render
deployment of the RC-5 candidate and completion of the Pending Operator Actions below. The pilot
deployment must not proceed until: (1) the backend is re-deployed (UAT-005 closed and verified via
live OpenAPI + no-token probes), (2) production env vars are confirmed (`DEBUG=false`, admin
secrets), and (3) Firestore Backups/PITR are enabled (data-protection for real users).

The RC-5 candidate itself is validated end-to-end (build, boot, auth enforcement, PDF generation,
46/46 regression) — no repository-side blockers remain.

---

## 12. Pending Operator Actions

1. **Trigger Render deployment using the RC-5 release candidate** — service
   `aviasafe-unified-platform` (repo `DHFactors/aviasafe-unified-platform`), Docker runtime,
   `backend/Dockerfile`, `dockerContext: backend`, `healthCheckPath: /live`. Build from the RC-5
   working tree (commit `4e306ce` + RC-1→RC-5 changes).
2. **Verify the deployment completed successfully** — live OpenAPI shows `security: [
   {"HTTPBearer":[]}]` on all admin POST endpoints and legacy `/check-data` + `/migrate-seed-data`
   are absent (404).
3. **Execute production smoke tests against the live environment** — `/health`, `/live`, `/ready`;
   invalid token → 401; protected surfaces → 403; one VSR + one MOR submission; dashboard load;
   risk-matrix classification; report generation (valid PDF).
4. **Confirm UAT-005 is resolved.**
5. **Record deployment timestamp and deployed commit hash.**
6. **Confirm the production environment matches the validated repository** (route inventory, admin
   security field, `DISABLE_DESTRUCTIVE_ENDPOINTS=true`, `DEBUG=false`).

---

*End of report. RC-6 begins only after approval and completion of the Pending Operator Actions.*
