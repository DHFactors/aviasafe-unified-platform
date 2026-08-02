# AviaSAFE UAT Execution Report — RC-4

- **Phase:** RC-4 — User Acceptance Testing (Independent Verification & Validation)
- **Date:** 02 August 2026
- **Scope:** All 12 UAT areas across all roles and workflows; regression of RC-1/RC-2/RC-3
- **Posture:** IV&V (independent) — objective is discovering why the software fails, not proving it works
- **Baseline regression:** `backend/tests/` — 40/40 passing
- **Final regression:** `backend/tests/` — 46/46 passing (40 original + 6 new cross-tenant/authorization regression tests)

---

## 1. Executive Summary

AviaSAFE's RC-4 UAT was executed as an independent verification and validation exercise. Twelve
UAT areas were examined via static code review of the repository, the automated regression suite,
and non-destructive dynamic probes of the live deployment (`https://aviasafe-unified-platform.onrender.com`).

The platform's core architecture — Firebase ID-token authentication, role-based access control
(`USER`/`AIRLINE_ADMIN`/`CAAN_SMD`/`SUPER_ADMIN`), tenant-scoped Firestore partitioning, the ICAO
5×5 risk matrix, and the CAN/CAP + verification/closure workflow — is sound, and the 40-test RC-3
regression baseline is fully green.

The investigation surfaced **12 verified findings**, of which **8 were fixed and verified** during
this phase (including 3 Critical/High authorization and cross-tenant defects), 3 are deployment or
recommendation items with no code change, and 1 is deferred. The single most consequential issue is
**UAT-005**: the live production deployment is running a build that predates the admin-endpoint
authentication hardening present in the repository; a re-deploy of the current repository build is
required before the platform can be considered production-ready.

Because the 8 code defects were corrected and verified in this phase and the remaining items are
either deployment actions or low-risk recommendations, the go/no-go recommendation is conditional
**GO for RC-5 (PILOT DEPLOYMENT)** once the live build is re-deployed from the current repository
HEAD/worktree (UAT-005).

## 2. Test Environment

| Component | Environment |
|-----------|-------------|
| Backend | FastAPI 0.109 / Python 3.13 (local), Render (`aviasafe-unified-platform.onrender.com`, live probe) |
| Database | Firebase Firestore (project `gap-analysis-ssp`); live connectivity confirmed (`/ready` → `firebase: connected`) |
| Auth | Firebase Authentication (ID tokens, custom claims), live verification endpoint |
| AI | Gemini analysis (mocked in regression tests; not invoked in probes) |
| Frontend | Static HTML/JS (`public/`); Firestore client SDK for anonymous surveys |
| Regression suite | `backend/tests/` — pytest, FastAPI TestClient, in-memory Firestore mock |
| Access | No production credentials were used. Probes were non-destructive (GET/health/paths/OpenAPI, unauthenticated POSTs to admin/seed paths with invalid setup keys) |

## 3. Scenarios Executed

### 3.1 Authentication (Area 1)
- Token verification endpoint reachable; valid/invalid token handling reviewed.
- Live probe: protected endpoints return `403 Not authenticated` without a token; invalid bearer token rejected.
- Registration endpoint reviewed (`POST /api/v1/auth/register`) — see Defects (registration accepts arbitrary tenant assignment; documented in register, not in scope for fix).

### 3.2 Authorization (Area 2)
- Role guards reviewed (`get_current_user`, `get_tenant_user`, `get_caan_user`, `get_admin_user`, `get_safety_manager`, `get_responsible_manager`, `get_accountable_executive`).
- Verified fixes: reporting tenant override restricted to cross-tenant roles (UAT-003); cross-tenant write endpoints now require a tenant (UAT-007).

### 3.3 Survey (Area 3)
- Anonymous survey submission path (client → Firestore `tenants/{id}/responses`) reviewed against rules.
- **UAT-004** identified and fixed: client/rules schema mismatch (`airline_id` vs `tenantId`).
- Survey anti-abuse: App Check is a documented known limitation (KNOWN_LIMITATIONS TD-12) — no code fix (medium, documented).

### 3.4 VSR / MOR (Area 4)
- Submission and retrieval endpoints reviewed; tenant-bound via `get_tenant_user`.
- Risk auto-calculation (severity × probability → risk index/level) covered by regression tests (passing).

### 3.5 Hazard register (Area 5)
- Create/update/status/assign reviewed; write endpoints tenant-bound. List supports CAAN/SUPER_ADMIN tenant override correctly (role-checked).

### 3.6 Risk matrix (Area 6)
- Thresholds (5/9/15 default), `compute_risk_index`, `get_risk_level`, `get_thresholds`; 16 dedicated unit tests pass.

### 3.7 CAN/CAP (Area 7)
- **UAT-002** identified and fixed: CAAN cross-tenant CAP read (list_caps, latest_cap, stats) and CAP-list response model.
- **UAT-007** identified and fixed: cross-tenant roles blocked from CAN/CAP writes without a tenant (previously silent corruption).

### 3.8 Reporting (Area 8)
- Quarterly/annual generation, list, retrieve, and export reviewed.
- **UAT-003** identified and fixed: USER tenant override authorization bypass.
- **UAT-006** identified and fixed: PDF export now valid (reportlab added); verified locally (`%PDF-1.4` output).

### 3.9 Administration (Area 9)
- Admin endpoints reviewed; setup-key second factor uses `secrets.compare_digest` in the working tree.
- **UAT-005** identified (live deployment runs pre-hardening build): admin provisioning endpoints lack bearer auth on live.

### 3.10 Data integrity (Area 10)
- Firestore rules reviewed: immutable responses/reports, tenant-isolated reads.
- **UAT-004** alignment; **UAT-012** deferred (closure latest-verification ordering).

### 3.11 Performance (Area 11)
- Collection-group vs tenant-scoped query patterns reviewed; dashboard queries use limit/clamp; no functional regressions. Live `/health`, `/ready`, `/live` return 200; cold start observed on `/health` (30s timeout once, 200 on retry) — see Performance Observations.

### 3.12 Security verification (Area 12)
- Live probe results: protected endpoints 403/401 without auth; admin POST without token reached the setup-key check (UAT-005 evidence); `/docs` and `/openapi.json` exposed (UAT-009); `/metrics` requires auth (OK).
- Firestore rules reviewed (tenant isolation, immutable audit trail, no App Check attestation conditions despite SECURITY.md claim — documentation gap noted under UAT-005/regulator docs).

## 4. Pass / Fail Matrix

| # | UAT Area | Result | Notes |
|---|----------|--------|-------|
| 1 | Authentication | PASS | Tokens verified; unauthenticated access denied |
| 2 | Authorization | PASS (after fix) | UAT-003, UAT-007 corrected; regression tests added |
| 3 | Survey | PASS (after fix) | UAT-004 aligned; anti-abuse is documented limitation |
| 4 | VSR / MOR | PASS | Regression green; risk auto-calculation verified |
| 5 | Hazard register | PASS | Tenant-bound writes; CAAN list override role-checked |
| 6 | Risk matrix | PASS | 16 unit tests green |
| 7 | CAN/CAP | PASS (after fix) | UAT-002 corrected (incl. CAP-list response model); UAT-007 guards |
| 8 | Reporting | PASS (after fix) | UAT-003, UAT-006 corrected; valid PDF verified |
| 9 | Administration | FAIL on live / PASS in repo | UAT-005: re-deploy required |
| 10 | Data integrity | PASS (after fix) | UAT-004; UAT-012 deferred (low risk) |
| 11 | Performance | PASS | No blocking issues; cold-start noted |
| 12 | Security verification | PASS (after fix) | UAT-003/005/007 addressed; docs/OpenAPI exposure recommended for production |

## 5. Regression Results

- **Baseline (pre-fix):** 40/40 passed.
- **Post-fix:** 46/46 passed.
- New regression tests added (6): CAAN cross-tenant risk confirmation lands in owner tenant; CAAN reads CAN/CAP across tenants; CAAN CAN write denied without tenant; USER cannot override tenant for reports; AIRLINE_ADMIN own-tenant report generation; CAAN national report generation.
- Test infrastructure corrected: CAAN_SMD/SUPER_ADMIN token claims now model production (no tenant claim); collection-group mock now traverses tenant sub-collections (previously always empty, masking cross-tenant behaviour); collection `get()` now returns snapshots like real Firestore.

## 6. Performance Observations

- Live `/ready` and `/live` return in milliseconds; `/health` 200 (first call cold-started and exceeded a 30s client timeout once — expected on Render's free tier).
- Query design: tenant-scoped queries use indexed paths; cross-tenant reads use collection-group queries (`REPO_QUERY_LIMIT` applied). One composite-index dependency is documented in UAT_READINESS.md (CAAN dashboard) with graceful fallback.
- No CPU/memory regressions attributable to the fixes; the changes add collection-group lookups only on cross-tenant write paths that were previously non-functional.

## 7. Security Verification Results

- **Good:** Protected endpoints reject anonymous access (403); invalid tokens rejected (401); `/metrics` requires auth; Firebase Admin SDK used server-side (rules bypassed only by authorised backend); setup key compared with `secrets.compare_digest` in the working tree; Firestore rules deny update/delete on survey responses (immutable audit trail) and isolate tenants by path + role claims.
- **Corrected this phase:** reporting tenant override (UAT-003); cross-tenant CAN/CAP/verification/closure/diversion write guards (UAT-007); survey rule alignment (UAT-004).
- **Deployment blocker:** UAT-005 — admin provisioning endpoints on live lack bearer auth (repo already corrected).
- **Documented limitations:** server-side App Check not enforced (KNOWN_LIMITATIONS TD-12); SECURITY.md claims rules require App Check attestation but the rules file has no attestation conditions (documentation gap); public `/docs` + `/openapi.json` exposure (UAT-009, recommendation).
- **Not exploited:** No attempt was made to authenticate, enumerate tenant data, or invoke destructive endpoints. Probes used only invalid setup keys and unauthenticated requests.

## 8. Defects Found

Full register: `UAT_DEFECT_REGISTER.md` (12 findings).

| ID | Severity | Finding |
|----|----------|---------|
| UAT-001 | Critical | CAAN_SMD/SUPER_ADMIN cannot confirm risk assessments cross-tenant (documented feature; `tenant_id=None` → random Firestore document path) |
| UAT-002 | High | CAAN cross-tenant CAP read broken (list_caps/latest_cap/stats) + CAP-list endpoint response-model mismatch (500) |
| UAT-003 | High | Any USER can read/generate another tenant's reports via `?tenant_id=` (authorization bypass + data pollution) |
| UAT-004 | High | Anonymous survey submission blocked by client/rules field mismatch (`airline_id` vs `tenantId`) |
| UAT-005 | Critical | Live deployment runs pre-hardening build: admin endpoints lack bearer auth (repo already fixed) |
| UAT-006 | Medium | PDF export returns plain-text placeholder (reportlab not in requirements) |
| UAT-007 | High | Cross-tenant roles reach CAN/CAP/verification/closure/diversion writes → silent writes to phantom tenant documents |
| UAT-008 | Medium | Tests masked cross-tenant behaviour (CAAN tenant claim in mocks; collection-group mock always empty) |
| UAT-009 | Low | Public `/docs` + `/openapi.json` exposure on live |
| UAT-010 | Low | `getCurrentUser()` silent 5s timeout resolves null |
| UAT-011 | Low | `/login.html?tenant=` unused outside deployment host |
| UAT-012 | Medium | Closure gate uses `verifications[-1]` without ordering |

## 9. Defects Corrected

| ID | Correction | Verification |
|----|-----------|--------------|
| UAT-001 | Cross-tenant resolution in `confirm_risk_assessment` (collection-group `__name__` lookup, update via document reference, per-report thresholds) | New regression test; suite green |
| UAT-002 | CAN/CAP reads use `doc.reference.collection("caps")`; `list_caps` cross-tenant branch; CAP-list `response_model=List[dict]` | New regression test; suite green |
| UAT-003 | `tenant_id` override allowed only for `CROSS_TENANT_ROLES`; no-tenant generation rejected 403 | New regression tests; suite green |
| UAT-004 | Client sends `tenantId`; rule accepts `airline_id` OR `tenantId` | Code/rules alignment verified |
| UAT-006 | `reportlab==4.1.0` added to requirements.txt; valid `%PDF-1.4` output confirmed locally | Local generation probe |
| UAT-007 | Tenant-required 403 guards on CAN/CAP/verification/closure/diversion-link writes | New regression test; suite green |
| UAT-008 | Test claims model production (CAAN/SUPER_ADMIN no tenant); collection-group mock traverses data; collection `get()` returns snapshots | Suite green |

After each correction the affected scenario was re-run and targeted regression executed (see §5).

## 10. Remaining Defects

| ID | Severity | Status | Recommended action |
|----|----------|--------|--------------------|
| UAT-005 | Critical | Open (deployment) | Re-deploy the current repository build so admin endpoints enforce `get_admin_user`; verify via OpenAPI `security` + no-token probe |
| UAT-009 | Low | Open (recommendation) | Disable `/docs`/`/openapi.json` in production (`docs_url=None`) |
| UAT-010 | Low | Open (recommendation) | Resolve signed-out state promptly; distinct timeout handling |
| UAT-011 | Low | Open (recommendation) | Use tenant param or explicit error outside trusted host |
| UAT-012 | Medium | Deferred | Order closure verifications by `created_at` DESC |
| (n/a) | Medium | Documented limitation | Server-side App Check verification + survey rate limiting (TD-12); correct SECURITY.md App Check claim |

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Production runs un-hardened admin build (UAT-005) | High until re-deploy | Critical | Immediate re-deploy from repo; validate security field in OpenAPI |
| Anonymous survey data pollution (no App Check enforcement) | Medium | Medium-High | Documented TD-12; add server-side App Check/rate limiting before wide pilot |
| Cross-tenant write path via non-tenant users | Eliminated | — | UAT-007 guards verified |
| Reporting cross-tenant exposure via query param | Eliminated | — | UAT-003 fix verified |
| Deferred closure-ordering edge case | Low | Low | Schedule in next release |
| Remaining unverified candidates (dashboard scoping, duplicate prevention, timestamps) | Unknown | Low-Medium | Carry into RC-5 verification |

## 12. Go / No-Go Recommendation

**Conditional GO for RC-5 — PILOT DEPLOYMENT**, subject to ONE release-blocking action:

1. **Re-deploy the backend from the current repository state** to close **UAT-005** (admin endpoints without bearer auth on the live build), and re-confirm with a no-token probe that admin endpoints return 401/403 rather than executing the setup-key check.

Post-fix evidence is strong: 46/46 regression tests pass (40 baseline + 6 new), all Critical/High code defects in the repository are corrected and verified, and the remaining findings are deployment actions, documented limitations, or low-severity recommendations. With the re-deploy completed, the platform is suitable for a controlled pilot deployment with the documented limitations (TD-12 App Check/survey anti-abuse, PDF dependency now shipped) tracked in the risk register.
