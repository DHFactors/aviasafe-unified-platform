# AviaSAFE Platform — Release Recovery Report (RR-1)

**Date:** 2 August 2026
**Phase:** RR-1 — Repository & Deployment Recovery
**Status:** **READY FOR REPOSITORY COMMIT**
**Trigger:** RC-5.5 FAILED — the validated RC-1…RC-5 changes existed only in the working tree and
were never committed; the deployed application did not represent the validated release candidate.

---

## 1. Executive Summary

RC-5.5 failed because of a **release management failure, not a software engineering failure**:
the entire validated release candidate (RC-1 security hardening, RC-2 functional corrections, RC-3
documentation, RC-4 UAT fixes, RC-5 operational documentation) exists **only in the working tree**
and has never been committed. Git HEAD (`4e306ce`) is the pre-RC-1 baseline, so any deployment
built from committed history reproduces the vulnerable build the RC-5.5 validation rejected.

RR-1 has verified, file by file, that the working tree is **complete and internally consistent**
and contains **no unverified or partially validated work**. A full release inventory (66 files: 45
modified, 1 deleted, 20 new) has been produced. A single atomic release commit plus the
`v1.0.0-rc5` tag is recommended so the repository becomes the single source of truth and the next
deployment is guaranteed to be byte-equivalent to the validated candidate.

The repository is now **ready to be committed**. No commit, deployment, or RC-5.5/RC-6 activity
has been performed; this phase stops after documentation, per the RR-1 final rule.

---

## 2. Repository Recovery

### 2.1 Baseline state

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `4e306ce chore(repo): stop tracking runtime logs` (pre-RC-1 baseline) |
| Remote | `origin https://github.com/DHFactors/aviasafe-unified-platform.git` |
| Existing tags | none |
| Staged changes | none |

### 2.2 Working-tree state (as reviewed)

- **46 tracked changes**: 45 modified + 1 deleted (`README-sms.md`).
- **20 untracked (new) files**: RC-3 documentation, RC-4/RC-5/RC-5.5 reports, `.env.example`,
  tenant-guide content, `backend/tests/test_risk_matrix.py`.
- **0 files omitted**: every working-tree change has been enumerated below and attributed to its
  release phase. Nothing validated exists only in the working tree outside this inventory.

### 2.3 Completeness verification performed

- `git status --porcelain=v1 --untracked-files=all` — full diff enumeration (see §3).
- `git diff --stat` — confirms 46 tracked files changed (944 insertions / 799 deletions).
- Confirmed the working tree **contains** the RC-1 hardening markers that the live deployment
  lacks:
  - `backend/app/core/config.py` adds env-only `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`,
    `DEFAULT_SEED_PASSWORD`, and `DISABLE_DESTRUCTIVE_ENDPOINTS: bool = True`.
  - `backend/app/routes/admin.py` now protects admin endpoints with `Depends(get_admin_user)`,
    uses `secrets.compare_digest` against `settings.SETUP_SECRET` (no hardcoded key), gates
    `/seed-demo-data` and `/create-seed-users` behind `DISABLE_DESTRUCTIVE_ENDPOINTS` (404), and
    **removed** the legacy `/check-data`, `/migrate-seed-data`, and `/auth/debug-verify` endpoints.
- Secrets hygiene confirmed: **no `.env` or `*.env` files are tracked** (`.gitignore` covers
  `.env`, `backend/.env`, `*.env`, `service-account.json`, `recaptch*`); no hardcoded
  `FIREBASE_PRIVATE_KEY`/service-account keys are tracked; `backend/.env.example` contains
  placeholders only and is safe to commit.

### 2.4 Recovery conclusion

The repository working tree **is** the validated release candidate. Recovery requires capturing it
verbatim in one commit (see §4) so that committed history and the validated candidate become the
same object. No validated work is missing from the inventory.

---

## 3. Release Inventory

All files that constitute the validated RC-1…RC-5 candidate (plus RC-5.5/RR-1 evidence). Grouped
by primary release phase. **46 tracked changes + 20 new files = 66 total.**

### 3.1 RC-1 — Security hardening (validated)

| File | Type | Change |
|---|---|---|
| `backend/app/core/config.py` | modified | Env-only `SETUP_SECRET`, provision/seed passwords, `DISABLE_DESTRUCTIVE_ENDPOINTS` |
| `backend/app/routes/admin.py` | modified | Remove legacy endpoints; `get_admin_user` auth; `compare_digest`; destructive 404 |
| `backend/app/routes/auth.py` | modified | Remove `/auth/debug-verify`; auth corrections |
| `backend/app/routes/can_cap.py` | modified | Endpoint auth/security fixes |
| `backend/app/routes/flight_diversions.py` | modified | Endpoint auth/security fixes |
| `backend/app/routes/reporting.py` | modified | Endpoint auth/security fixes |
| `backend/app/routes/reports.py` | modified | Endpoint auth/security fixes |
| `backend/app/routes/verification.py` | modified | Endpoint auth/security fixes |
| `backend/app/services/can_cap_service.py` | modified | Service-layer fixes |
| `backend/app/services/hazard_service.py` | modified | Service-layer fixes |
| `backend/app/services/report_service.py` | modified | Service-layer fixes |
| `backend/app/services/risk_matrix.py` | modified | Risk matrix fixes |
| `backend/requirements.txt` | modified | Dependency updates (reportlab 4.1.0) |
| `firestore/firestore.rules` | modified | Firestore security rules |
| `public/js/firebase.js` | modified | App Check / key handling |
| `docs/SECURITY.md` | modified | Security documentation |

### 3.2 RC-2 — Functional corrections (validated)

| File | Type | Change |
|---|---|---|
| `backend/seed/config.py` | modified | Seed config corrections |
| `backend/seed/generator.py` | modified | Seed generator corrections |
| `backend/seed/operators.py` | modified | Seed operator data corrections |
| `backend/seed/reports.py` | modified | Seed report data corrections |
| `backend/seed/users.py` | modified | Seed user data corrections |
| `scripts/provision-20-airlines.js` | modified | Provisioning script corrections |
| `scripts/seed/check_seed.py` | modified | Seed verification corrections |
| `scripts/seed/run_seed.py` | modified | Seed runner corrections |
| `backend/tests/test_risk_assessment_lifecycle.py` | modified | Lifecycle tests + RC-4 cross-tenant tests |
| `backend/tests/test_risk_matrix.py` | **new** | Risk matrix unit tests |
| `public/js/hazards.js` | modified | Hazard UI fixes |
| `public/portal/dashboards/caan.js` | modified | CAAN dashboard fixes |
| `public/portal/dashboards/dashboard.js` | modified | Dashboard fixes |
| `public/portal/survey/app.js` | modified | Survey fixes |
| `design/risk-assessment-v1.md` | modified | Design corrections |
| `docs/HAZARD_TAXONOMY.md` | modified | Taxonomy corrections |
| `docs/UAT_READINESS.md` | modified | UAT readiness updates |
| `tests/e2e/e2e_auth.py` | modified | E2E auth tests |
| `tests/e2e/e2e_diag.py` | modified | E2E diagnostics tests |
| `tests/e2e/e2e_setup_claims.py` | modified | E2E setup/claims tests |
| `tests/e2e/e2e_test.py` | modified | E2E tests |
| `tests/e2e/e2e_test2.py` | modified | E2E tests |
| `tests/e2e/test_dash.py` | modified | E2E dashboard tests |
| `tests/README.md` | modified | Test documentation |
| `README.md` | modified | Root README (restored text content) |
| `DEMO_GUIDE.md` | modified | Demo guide |
| `ROADMAP.md` | modified | Roadmap updates |
| `PROJECT_STATUS.md` | modified | Status updates |
| `README-sms.md` | **deleted** | Superseded SMS doc (content moved/obsolete) |

### 3.3 RC-3 — Documentation (validated)

| File | Type |
|---|---|
| `docs/ADMIN_GUIDE.md` | **new** |
| `docs/API.md` | **new** |
| `docs/ARCHITECTURE.md` | **new** |
| `docs/DEPLOYMENT.md` | **new** |
| `docs/INSTALLATION.md` | **new** |
| `docs/KNOWN_LIMITATIONS.md` | **new** |
| `docs/OPERATIONS.md` | **new** |
| `docs/ONBOARDING_CREDENTIALS_20_AIRLINES.md` | modified |
| `docs/WELCOME_EMAIL_20_AIRLINES.md` | modified |
| `public/docs/tenant-guide/01-getting-started/1.0-overview.md` | **new** |
| `public/docs/tenant-guide/02-account-setup/1.0-account-profile-setup.md` | **new** |
| `public/docs/tenant-guide/03-safety-reporting/1.0-vsr-mor-submission.md` | **new** |
| `public/docs/tenant-guide/manifest.json` | **new** |
| `public/docs/tenant-guide/templates/STEP_DOCUMENTATION_TEMPLATE.md` | **new** |
| `backend/.env.example` | **new** (safe template, placeholders only) |

### 3.4 RC-4 — UAT fixes & evidence (validated)

| File | Type |
|---|---|
| `UAT_EXECUTION_REPORT.md` | **new** |
| `UAT_DEFECT_REGISTER.md` | **new** |
| `backend/tests/test_risk_assessment_lifecycle.py` | modified (6 new cross-tenant tests — 46/46 pass) |

### 3.5 RC-5 — Operational documentation (validated)

| File | Type |
|---|---|
| `PILOT_READINESS_REPORT.md` | **new** |
| `RELEASE_NOTES_RC5.md` | **new** |
| `PROJECT_STATUS_REPORT_02AUG2026.md` | **new** |

### 3.6 RC-5.5 / RR-1 — Validation evidence

| File | Type |
|---|---|
| `LIVE_DEPLOYMENT_VALIDATION_REPORT.md` | **new** (RC-5.5 evidence, FAILED verdict) |
| `RELEASE_RECOVERY_REPORT.md` | **new** (this report) |

---

## 4. Commit Recommendation

### 4.1 Structure: single atomic release commit (recommended)

A **single release commit** is explicitly recommended over a phase-grouped commit series.

Rationale:
1. **Atomicity = correctness.** The validated candidate is the working tree as a whole. One commit
   guarantees the deployed artifact exactly matches the validated, tested state (46/46 tests,
   Docker-built candidate, hardening verified).
2. **No reconstructable intermediate states.** RC-1…RC-5 were developed without intermediate
   commits; splitting now would require reverse-engineering phase boundaries with no authoritative
   record, risking an incorrect or non-building intermediate commit.
3. **Auditability.** A single well-messaged release commit plus a release tag gives a clear,
   reproducible release object for review, deployment, and rollback.

Proposed commit (when approved):

```
release: validate AviaSAFE RC-1 through RC-5 release candidate (v1.0.0-rc5)

Captures the entire validated RC-1..RC-5 working tree as the single source of
truth for the release candidate:

- RC-1 security hardening: env-only SETUP_SECRET + compare_digest, admin auth
  (get_admin_user), destructive endpoints gated (404), legacy /check-data,
  /migrate-seed-data and /auth/debug-verify removed, firestore rules, SECURITY.md.
- RC-2 functional corrections: seed pipelines, scripts, risk lifecycle tests.
- RC-3 documentation: ADMIN/API/ARCHITECTURE/DEPLOYMENT/INSTALLATION/KNOWN_LIMITATIONS/
  OPERATIONS guides, tenant-guide content, .env.example.
- RC-4 UAT: 8 fixes verified, 46/46 regression incl. 6 new cross-tenant tests,
  UAT_EXECUTION_REPORT.md, UAT_DEFECT_REGISTER.md (UAT-005 OPEN pending deploy).
- RC-5 operational docs: PILOT_READINESS_REPORT.md, RELEASE_NOTES_RC5.md,
  PROJECT_STATUS_REPORT_02AUG2026.md.

No secrets are tracked (.env ignored; .env.example is placeholders only).
Deploys from this commit are expected to satisfy the RC-5.5 verification checklist.
```

(Commit to be executed only upon explicit approval — not performed during RR-1.)

### 4.2 Alternative (not recommended)

A 5-commit phase series (one per RC) is possible but **not recommended** because phase boundaries
cannot be reconstructed with authority from the uncommitted working tree.

---

## 5. Release Tag Recommendation

**Recommended tag: `v1.0.0-rc5`**

- Signed/annotated tag (annotated at minimum) on the release commit.
- Matches `RELEASE_NOTES_RC5.md` and provides the immutable deployment baseline for backend
  (Render) and frontend (Firebase Hosting) releases.
- Future RC-6 tag (after approval): `v1.0.0-rc6`.
- Push both branch and tag to `origin` after approval.

---

## 6. Deployment Checklist

Step-by-step runbook for deploying the committed candidate. **Do not execute until the release
commit and tag exist and are approved.**

### 6.0 Preconditions (Release Management)

- [ ] RR-1 report accepted; approval granted to commit.
- [ ] Release commit `release: validate AviaSAFE RC-1 through RC-5...` created on `main`.
- [ ] Tag `v1.0.0-rc5` created (annotated) and pushed with the branch to `origin`.
- [ ] Confirm `git status` clean on the release commit (nothing committed after the tag).

### 6.1 Backend — Render deployment

- [ ] Render service: confirm connected repo/branch = `main` at tag `v1.0.0-rc5` (build from the
      tag, not HEAD).
- [ ] Confirm Render build root = repository root; Dockerfile used (`backend` service container).
- [ ] Trigger deploy; wait for successful build (`Build succeeded`).
- [ ] Capture the deployed commit hash in the Render dashboard (must equal the release commit).

### 6.2 Environment variables & secrets (Render)

- [ ] `FIREBASE_PROJECT_ID` — set (real project id).
- [ ] `FIREBASE_CLIENT_EMAIL` — set.
- [ ] `FIREBASE_PRIVATE_KEY` — set to the real service-account key (multi-line, properly escaped;
      verify no surrounding quotes are introduced by the dashboard).
- [ ] `SETUP_SECRET` — set to a strong, non-public value (never the old hardcoded key). Required.
- [ ] `DEFAULT_PROVISION_PASSWORD` — set (used by `/provision-airlines`).
- [ ] `DEFAULT_SEED_PASSWORD` — set (used by seed pipeline).
- [ ] `DISABLE_DESTRUCTIVE_ENDPOINTS` — set `True` (production).
- [ ] `GEMINI_API_KEY` / `AI_API_KEY` — set as applicable.
- [ ] `REDIS_ENABLED` — set per `render.yaml` value.
- [ ] Confirm **no** `SETUP_SECRET` default exists in code (config default is `None`).

### 6.3 Frontend — Firebase Hosting deployment

- [ ] Build frontend assets (if applicable) with production config.
- [ ] Set Firebase Hosting project to the deployed project id for the app.
- [ ] `firebase deploy --only hosting` (release from `public/`).
- [ ] Confirm site live at `https://gap-analysis-ssp.web.app` (all paths return 200).
- [ ] Fix backend CORS allow-list to the actual reachable frontend origin(s) if the URL changes.

### 6.4 Post-deployment verification (immediate)

- [ ] Backend `/health`, `/live`, `/ready` return 200.
- [ ] Backend `/openapi.json` admin POST `security: [{"HTTPBearer":[]}]` (no `security: null`).
- [ ] Legacy `/check-data`, `/migrate-seed-data`, `/auth/debug-verify` return 404.
- [ ] `/seed-demo-data`, `/create-seed-users` return 404 (destructive endpoints disabled).
- [ ] Frontend root and main routes return 200 (not "Site Not Found").
- [ ] Execute the full §7 verification checklist and record results.

### 6.5 Rollback

- [ ] Backend: Render → Deploy → select previous working release (pre-candidate image) and redeploy.
- [ ] Frontend: Firebase Hosting → previous release (channels/versions list) → rollback.
- [ ] If config is the cause (env/secret), correct the variable and redeploy the same tag — no
      code change required.
- [ ] Document the rollback trigger, actions, and outcome in `PROJECT_STATUS_REPORT_02AUG2026.md`.

---

## 7. Verification Checklist

Executable immediately after deployment (Phase 5 / §6.4). Intended to confirm the live build
matches the validated candidate and to close UAT-005.

### 7.1 Backend version verification

- [ ] Render dashboard shows the release commit (tag `v1.0.0-rc5`) as the deployed commit.
- [ ] `/health` → `{"status":"healthy","firebase":"connected","version":"1.0.0"}`.

### 7.2 Frontend verification

- [ ] `https://gap-analysis-ssp.web.app/` returns 200 (site online, not "Site Not Found").
- [ ] Main portal routes (`/portal/...`, dashboard, survey) return 200.
- [ ] Tenant-guide pages return 200.

### 7.3 Protected endpoint verification (no token)

- [ ] No-token call to every admin POST returns **403** (not 422 — auth is enforced before body
      validation).
- [ ] `/api/v1/auth/verify` with invalid token → 401.
- [ ] All protected surfaces (reports, verification, can_cap, diversions) → 403.

### 7.4 Smoke tests

- [ ] `/live` alive, `/ready` ready, `/health` healthy.
- [ ] Security headers present: HSTS, X-Content-Type-Options, X-Frame-Options: DENY,
      X-XSS-Protection, Referrer-Policy, Permissions-Policy.

### 7.5 Security verification

- [ ] Legacy endpoints `/check-data`, `/migrate-seed-data`, `/auth/debug-verify` → **404**.
- [ ] `/seed-demo-data`, `/create-seed-users` → **404** (DISABLE_DESTRUCTIVE_ENDPOINTS).
- [ ] Admin POST in `/openapi.json` shows `security: [{"HTTPBearer":[]}]` (no `security: null`).
- [ ] No public `SETUP_SECRET` default: key derived from env only; attempts with the old
      `aviasafe-e2e-setup-2026` value and no valid admin token → 403.

### 7.6 Tenant isolation

- [ ] Data created/read as tenant A is invisible to tenant B (validated by the 6 cross-tenant
      regression tests — rerun locally against the tagged commit if needed).
- [ ] Cross-tenant probe (authenticated A calling B-scoped resource) → 403/empty.

### 7.7 Admin endpoint validation

- [ ] Admin provisioning flow requires a valid SUPER_ADMIN Firebase ID token **and** `SETUP_SECRET`.
- [ ] `/provision-airlines` returns 403 without credentials; 200 only with both factors.
- [ ] Weak/missing `SETUP_SECRET` in env → endpoint refuses (config default `None`).

### 7.8 UAT-005 verification (closure criteria)

UAT-005 (Admin API authorization bypass) is **CLOSED** only when ALL of the following hold on the
live environment:
- [ ] No-token admin POST → **403**.
- [ ] Legacy admin/debug endpoints → **404**.
- [ ] `security: HTTPBearer` on all admin POSTs in `/openapi.json`.
- [ ] Destructive endpoints → **404**.
- [ ] Frontend reachable at `https://gap-analysis-ssp.web.app` (200) so pilot users can access the
      portal.
- [ ] Update `UAT_DEFECT_REGISTER.md`: UAT-005 → status **CLOSED**, with re-verification evidence
      and date.

---

## 8. Remaining Risks

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R-1 | Commit/tag never executed or tag points to wrong commit | Critical | §4/§6.0 gate: RR-1 approval required; verify deployed commit == tagged commit |
| R-2 | `FIREBASE_PRIVATE_KEY` escaping breaks startup or auth after deploy | High | §6.2 double-check; verify `/health` firebase: connected post-deploy |
| R-3 | Frontend origin mismatch → CORS blocks portal | High | §6.3 confirm reachable URL and CORS allow-list |
| R-4 | `SETUP_SECRET` reused public value from old build | High | §6.2 set strong unique value; RC-1 code never falls back to hardcoded key |
| R-5 | Post-deploy verification not completed before UAT-005 closed | High | §7.8 closure criteria are mandatory; evidence recorded |
| R-6 | No automated Firestore backups/PITR | Medium | Out of RR-1 scope; operator action tracked from RC-5.5 |
| R-7 | `/docs` + `/openapi.json` exposed (UAT-009) | Low | Tracked as deferred/accepted in UAT register |

---

## 9. Recommendation

1. **Accept this report.** The repository is verified as the complete validated RC-1…RC-5
   candidate with no omissions and no tracked secrets.
2. **Approve the release commit** (single atomic commit, message in §4.1) and the tag
   `v1.0.0-rc5` (§5). Commit and push to `origin/main` — **not performed during RR-1**.
3. **Approve execution of the §6 deployment checklist** (backend → frontend → env/secrets →
   verification) and the §7 verification checklist immediately after deploy.
4. **Re-run the RC-5.5 validation** against the deployed tag. Only then close UAT-005 and
   re-declare the phase result (RC-5.5 PASSED) and proceed to RC-6.

**Phase declaration: READY FOR REPOSITORY COMMIT**
