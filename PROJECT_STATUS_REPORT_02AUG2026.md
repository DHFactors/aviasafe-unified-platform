# PROJECT_STATUS_REPORT — 02 AUGUST 2026

**Project:** AviaSAFE SMS Platform (Safety-Health / surveysms)
**Report date:** 2026-08-02
**Author:** Engineering Lead (project handover)
**Repo HEAD:** `4e306ce` — `chore(repo): stop tracking runtime logs` (2026-07-30 10:53 +0545)
**Branch:** `main` (tracking `origin/main`)
**Self-declared status (PROJECT_STATUS.md):** "Production-Ready (Release Candidate 1.0)"

> This report is a **read-only assessment**. No source files were modified. All conclusions are
> cross-checked against the actual implementation in the repository. Facts are distinguished from
> observations and assumptions throughout. Every claim cites evidence (file:line).

---

## Current Status

**Status:** Release Candidate

| Phase | Description | State |
|---|---|---|
| RC-1 | Security Hardening & Release Blockers | COMPLETE |
| RC-2 | Functional Corrections & Regression Validation | COMPLETE |
| RC-3 | Documentation & Operational Readiness | COMPLETE |
| RC-4 | UAT Readiness | COMPLETE (conditional) |
| RC-5 | Pilot Preparation | COMPLETE (conditional on operator re-deploy) |
| RC-5.5 | Live Deployment Validation | **FAILED — DEPLOYMENT VALIDATION FAILED** |
| RR-1 | Repository & Deployment Recovery | **READY FOR REPOSITORY COMMIT** (awaiting approval) |
| RC-6 | Production Readiness Review | Next (blocked) |

**Overall Progress:**

- Feature Development ............. 100%
- Release Candidate Hardening ..... 83% (5/6 phases complete; **RC-5.5 validation failed — deploy corrections required**)
- Release Recovery (RR-1) ......... Documentation complete; **repository ready for commit** (pending approval)
- Estimated Production Readiness .. ~85% (blocked by failed deployment validation; corrections gated on commit + re-deploy)

---

## 1. Executive Summary

AviaSAFE is a multi-tenant aviation Safety Management System (SMS) intelligence platform for
Nepal, aligned with ICAO Annex 19 / Doc 9859 and CAAN CAR-19. It collects three data sources —
**Safety Culture Survey**, **Voluntary Safety Reporting (VSR)**, **Mandatory Occurrence Reporting
(MOR)** — and presents them on an **Airline Dashboard** ("how healthy is our SMS / what are our top
risks") and a **CAAN SSP Dashboard** (cross-tenant industry aggregation).

The project is **functionally feature-complete for a prototype/Release Candidate**. The backend is a
well-structured FastAPI + Firebase Admin (Firestore) service with 143 routes, a clean service
layer, working RBAC, tenant isolation, AI-assisted risk assessment, Redis-backed rate limiting,
reporting/PDF export, and a 24-test green unit suite. The frontend has 29+ HTML pages with a
centralized Firebase/Auth/API client. It is **live** on Firebase Hosting
(`gap-analysis-ssp.web.app`) and Render (`aviasafe-unified-platform.onrender.com`).

Development **stopped on 30 July 2026** mid-stream in a "hardening/UAT-preparation" batch. Two
items are **uncommitted** (live reCAPTCHA key swap in `public/js/firebase.js`, tenant-guide
documentation framework with only step 01 written), and the documented next phase (P1 **UAT**,
P3/P4 **airline/CAAN pilots**, P5 **Cloud Run go-live**) has not begun.

**Bottom line:** the product is *UAT-capable* but **not production-safe as committed**. A
hardcoded admin secret (`aviasafe-e2e-setup-2026`) gates seven unauthenticated, dangerous API
endpoints on the live backend (privilege escalation, database wipe, server filesystem write),
credentials are hardcoded in source and documentation, and the headline risk-matrix configuration
endpoint (`PUT /risk-matrix`) currently crashes. The highest-priority next task is **critical
security and release-blocker remediation**, followed by the charter's Phase 6A **survey
re-alignment** and the risk-matrix threshold plumbing.

---

## 2. Current Project Status

| Dimension | Assessment |
|---|---|
| **Overall completion** | ~85% of the prototype/Release-Candidate scope; ~60–65% toward true production readiness |
| **Current phase** | Post-development hardening & UAT preparation (feature-complete; pre-pilot) |
| **Overall health** | Good engineering structure; degraded by critical security debt and several dead-code/incorrect paths |
| **Major accomplishments** | See §4 and Feature Matrix §6 |
| **Remaining work** | Security remediation; survey charter re-alignment; risk-matrix plumbing; CI/CD + Cloud Run; docs steps 02–03; UAT and pilots |

### What has been completed (evidence-grounded)

- **Backend API** — 9 routers, 143 routes; dual `/api/v1/...` + legacy `/api/...` prefixes
  (`backend/app/main.py:101-124`).
- **Authentication / RBAC** — Firebase ID-token verification (RS256) + 4 custom-claim roles
  (`USER`, `AIRLINE_ADMIN`, `CAAN_SMD`, `SUPER_ADMIN`) enforced via 6 dependency guards
  (`backend/app/middleware/auth.py:47-167`).
- **Tenant isolation** — every collection under `/tenants/{tenant_id}/...`; rules enforce
  `isOwnTenant()` / cross-tenant CAAN read-only (`firestore/firestore.rules`).
- **Core modules** — VSR, MOR, Hazard Register, CAN/CAP, Verification & Closure, Quarterly/Annual
  Reporting + PDF export, Flight Diversions, Airline & CAAN dashboards, Admin portal.
- **AI integration** — Gemini (`gemini-2.0-pro-exp-02-05`) narrative analysis with severity/
  probability *suggestion* (never authoritative); `mock_analysis` fallback
  (`backend/app/services/gemini.py:86-268`).
- **Platform hardening** — Redis (Upstash) + in-memory rate limiting, security headers, App Check
  (client-side), Firestore rules hardening, Prometheus `/metrics`, structured logging.
- **Seed dataset** — 6 operators / 20 provisioned; 930 surveys, 620 VSR, 245 MOR; deterministic,
  idempotent; timestamp and tenant-ID migrations run.
- **Tests** — 24 pytest unit tests all pass (verified run: `24 passed`); E2E suite (10 scenarios)
  against the live API.

### What is partial / broken / missing

- **Security (critical):** hardcoded admin secret; open debug endpoints; hardcoded credentials in
  source and docs; fake Firebase keys + mock auth bypasses in `public/portal`.
- **Survey vs Product Charter:** live questionnaire uses *custom culture dimensions* (19 q,
  sections A–D), not the charter's 4 ICAO components / 12 elements; **no backend survey endpoint**
  exists; frontend writes to `surveyResponses` while seed writes to `surveys`.
- **Risk matrix:** `PUT /risk-matrix` raises `TypeError` (missing positional arg); tenant
  thresholds are stored but **never used** by scoring; reports and hazards use **different**
  threshold schemes.
- **CAAN dashboard:** `get_caan_trends` / `get_caan_benchmark` / `get_admin_usage` return
  placeholder `None` values (`backend/app/services/dashboard_service.py`).
- **Deployment:** two contradictory `render.yaml` files; no active CI/CD (only a disabled workflow);
  Cloud Run is configured but not deployed; `package.json` `build`/`test` are no-op stubs.
- **Docs:** tenant-guide steps 02 and 03 not written; root `README.md` is essentially empty.

---

## 3. Architecture Summary

### 3.1 System topology

```
Browser (Firebase Hosting — gap-analysis-ssp.web.app)
  public/     29+ HTML pages (login, safety, caan, admin, hazards, can_cap, ...)
  public/js    firebase.js → App Check → Auth → api/client.js (JWT Bearer)
               domain JS: dashboard, vsr, mor, reports, hazards, can_cap, verification, diversions
  src/         Astro marketing pages (index + BaseLayout) — separate concern
        │ HTTPS (Bearer JWT)
        ▼
Backend (FastAPI — Render free tier / target Cloud Run)
  app/main.py            app wiring, CORS, 3 middleware, exception handlers
  app/routes/            9 routers (auth, reports, dashboard, admin, hazards, can_cap,
                         verification, reporting, flight_diversions)
  app/services/          12 modules (Repository, DashboardService, ReportService, HazardService,
                         CanCapService, VerificationService, FlightDiversionService, ReportGenerator,
                         Gemini, RiskMatrix, MetricsService, PDFGenerator)
  app/models/            11 Pydantic models
  app/middleware/        auth.py (token → claims → tenant), rate_limit.py (Redis decorator)
  app/core/              config.py (pydantic-settings), security.py (headers + in-memory limiter),
                         metrics.py (Prometheus), logging.py (loguru + request middleware)
  app/firebase.py        Admin SDK init, token verify, custom-claims helper
        │
        ▼
Firestore (gap-analysis-ssp, nam5)          + Google Gemini API + Upstash Redis
```

### 3.2 Data model (Firestore)

```
/tenants/{tenant_id}/
    metadata/info            tenant config (safety_manager, survey_config, ...)
    metadata/risk_matrix     ICAO 5×5 config (severity/probability labels, thresholds)
    responses/{id}           survey responses (public create, immutable)  [930 seeded]
    reports/{id}             VSR reports (public create, immutable)        [620 seeded]
    mor/{id}                 MOR reports (auth create)                    [245 seeded]
    hazards/{id}             hazard register (full tenant CRUD)
    can_cap/{id}             CAN + CAP workflow
    verification/{doc}       verification & closure
    flight_diversions/{doc}  diversion records
/analytics/{doc}             CAAN aggregate (CAAN_SMD / SUPER_ADMIN)
/public_responses/{doc}      public survey
/users/{uid}                 user profiles
```

**Report fields (VSR/MOR)** — verified against charter:
- ✅ VSR input (`models/report.py:103-153`) contains **no** `corrective_actions` /
  `lessons_learned` / `safety_action_required` (charter-compliant).
- ✅ MOR input (`models/report.py:155-288`) keeps `investigation_status` (charter-compliant).
- 🟡 **Leftover references:** `metrics_service.py:230-237` still counts `corrective_actions` KPIs
  (will always be 0); `report_service.py:266-279` writes `reviewed_by`/`reviewed_at` on
  risk-assessment confirmation.

### 3.3 Security model

- **Auth:** Firebase Auth; backend verifies ID tokens via Admin SDK
  (`backend/app/firebase.py:82-99`). `check_revoked=False` (deliberate, avoids clock-skew).
- **RBAC roles:** `USER` (submit/read own tenant), `AIRLINE_ADMIN` (tenant management + safety
  manager duties), `CAAN_SMD` (cross-tenant read + assessment confirm), `SUPER_ADMIN` (system-wide).
- **Claims resolution:** token custom claims → fallback Firestore tenant email lookup
  (`auth.py:24-45,70-76`); `tenant_id` underscore→hyphen normalization (`auth.py:64-68`).
- **Firestore rules:** public-create for VSR/responses; tenant-isolated reads; CAAN read-only
  across tenants; SUPER_ADMIN writes (`firestore/firestore.rules`).
- **Transport/application:** HSTS, nosniff, frame-deny, XSS, referrer, permissions policy
  (`core/security.py`); client-side App Check (reCAPTCHA v3, live key uncommitted).

### 3.4 Deployment

| Component | Current (live) | Target (commercial) |
|---|---|---|
| Frontend | Firebase Hosting `gap-analysis-ssp.web.app` | Firebase Hosting (Blaze) `sms.aviasafesystems.com` |
| Backend | Render free tier `aviasafe-unified-platform.onrender.com` | Cloud Run (`backend/cloudrun.yaml`, 512MB/1CPU/1-10) |
| Database | Firestore nam5 | Firestore |
| AI | Google Gemini | Gemini |
| Rate limit | Upstash Redis | Upstash Redis |
| Container | `backend/Dockerfile` (python:3.11-slim) + `docker-compose.yml` | Cloud Run |

⚠️ **Two Render definitions exist and conflict:** root `render.yaml` (bare Python, workingDir
`backend`, uvicorn app.main) vs `backend/render.yaml` (Docker service). Both name the service
`aviasafe-api`. Only one can be authoritative on Render.

### 3.5 Testing strategy

- **Unit/integration:** pytest against in-process `TestClient` with a full Firestore+Gemini mock
  stack (`backend/tests/`); 24 tests, all pass.
- **E2E:** Python scripts hitting the **live** Render API (`tests/e2e/*.py`), 10 scenarios, token
  acquisition helpers.
- **Firebase admin scripts:** `scripts/firebase/*.js` for claims/user management.
- **Seed utilities:** `scripts/seed/run_seed.py`, `check_seed.py`.

---

## 4. Repository Assessment (directory-by-directory)

| Path | Purpose | Assessment |
|---|---|---|
| `backend/` | FastAPI application | Strong layering (routes → services → repository). Contains **stale artifacts**: `database.py` is a dead Supabase stub; `backend/firestore.indexes.json` is unused (root file is authoritative); `backend/render.yaml` conflicts with root `render.yaml`. |
| `backend/app/core/` | Config, security, metrics, logging | Clean. `config.py` pydantic-settings with .env loading; `security.py` headers + in-memory limiter. |
| `backend/app/routes/` | API controllers | Complete. Contains 7 debug/admin endpoints gated only by hardcoded `SETUP_SECRET` (admin.py:96); `PUT /risk-matrix` broken (admin.py:86). |
| `backend/app/services/` | Business logic | Clean separation; `dashboard_service.py` has placeholder `None` values; `risk_matrix.py` has dead functions + two inconsistent threshold schemes. |
| `backend/app/models/` | Pydantic schemas | Charter-compliant VSR/MOR. `error.py`, `report.py` etc. No survey model (survey has no backend path). |
| `backend/seed/` | Deterministic seed generator | Uses 12 ICAO elements + 4 pillars correctly (`seed/config.py:6-56`); timestamps mostly correct (two ISO-string leftovers). |
| `backend/tests/` | Unit tests | 24 tests, all green; well-mocked risk-assessment lifecycle suite. |
| `functions/` | Cloud Functions | **Empty** (`functions/src/` has zero files) — declared "not required yet". |
| `firestore/` | Security rules | Solid; see §6 for findings. |
| `firestore.indexes.json` (root) | Composite indexes | 6 indexes; **camelCase** fields matching frontend survey schema — mismatches backend snake_case queries (fallback workarounds exist). |
| `public/` | Frontend (Firebase Hosting) | 29+ pages, centralized Firebase/Auth/API client. Contains deprecated duplicates (`public/dashboard/`, `public/survey/` v2), mock portal code with **fake Firebase key**, and untracked `docs/tenant-guide/`. |
| `public/js/` | Core + domain JS | Good; `tenant.js` depends on uninitialized `db` global; `vsr.js`/`mor.js` payload keys differ from `report.js`. |
| `public/docs/` | Tenant onboarding docs (docs-as-code) | Framework + step 01 only (**untracked**); steps 02–03 empty in manifest. |
| `src/` | Astro marketing | `index.astro` + `BaseLayout.astro`; Tailwind. Unrelated to product, built separately. |
| `scripts/` | Firebase admin + seed + provisioning | `provision-20-airlines.js` hardcodes a password (value redacted RC-3); `fix-tenant-ids.py` migration. |
| `tests/` | E2E scripts | `e2e/` + README. Two E2E scripts **contradict** each other on risk-matrix RBAC (403 vs 200). `e2e_tokens.json` contains stale, mislabeled tokens. |
| `docs/` | Product docs | `UAT_READINESS.md` (28 Jul), `HAZARD_TAXONOMY.md`, `SECURITY.md` (outdated/Supabase-era claims), onboarding credential docs (**contain plaintext passwords**). |
| `design/` | Design specs | `risk-assessment-v1.md` — matches implemented design; note configurable thresholds were spec'd but not plumbed. |
| `.github/workflows/` | CI/CD | Only `deploy.yml.disabled` (Astro GitHub Pages, no test job). **No active CI/CD.** |
| Root config | `package.json`, `astro.config.mjs`, `firebase.json`, `render.yaml`, `docker-compose.yml` | `package.json` build/test are echo stubs; two competing render.yaml. |

---

## 5. Development History & Timeline Reconstruction

### Original vision
AviaSAFE Systems aviation-only SMS intelligence platform (per `PROJECT_CHARTER.md`): Survey
measures SMS capability, VSR reveals hazards, MOR reveals occurrences; CAAN monitors SSP
effectiveness in real time. Early repo traces (2026-07-03 era) show a **Supabase/PostgreSQL**
architecture (`README-sms.md`, `backend/app/database.py`, `docs/SECURITY.md`) that was abandoned
in favor of **Firebase/Firestore**.

### Milestones (from git history)

| Date | Milestone | Evidence |
|---|---|---|
| 2026-06-14 | Astro marketing platform initialized; GitHub Pages CI injected then disabled | commits `d8e17c9` → `b4cb7d4`, `98966b6` |
| 2026-07-03 | Supabase-era backend scaffolding (FastAPI, stubs) | `README-sms.md`, `database.py` header dates |
| 2026-07-18 | **Monorepo merge** — SaaS portal into marketing frontend | `9b0fbf9`; Astro downgraded to v5 |
| 2026-07-26 | Phase 1 — Firestore security rules authorization model fix | `a01c8f9`, `d075442` |
| 2026-07-27 | **Phase 4 completion** — login bugfix, Render deploy, 14/14 tests passing; VSR complete (6-section form, ADREP taxonomy); ECCAIRS MOR/VSR forms; dashboard consistency; CAAN collectionGroup dashboard; survey period management; Firebase CDN scripts | `066aba7`, `e549f90`, `2c9ce68`, `765c86a`, `a76b30c`, `428f9ce`, `14a60d0` |
| 2026-07-28 | **Modules milestone** — Verification & Closure, Reporting & PDF Export, Flight Diversions completed (`f97f260`); batch provisioning of 20 airlines + onboarding docs; risk assessment lifecycle; CAAN dashboard hardening; auth claims fixes; **UAT Readiness Report** | `f97f260`, `cdc37f5`, `9e27c3d`, `b93c538`, `6cb5b57`, `a1b422a`, docs/UAT_READINESS.md |
| 2026-07-29 | **Hardening batch** — seed data migration (tenant IDs, timestamps), Redis/Upstash rate limiting (replacing slowapi), App Check + Firestore rules + security headers hardening, demo seed endpoints, render.yaml updates | `f2790b7` … `5b39427` |
| 2026-07-30 | **Final commit(s)** — repo reorganisation (scripts → `tests/e2e`, `scripts/firebase`, `scripts/seed`), log-level demotion, remove node_modules/runtime logs from index; **then stopped** | `70a96b6`, `e04884d`, `957e8ce`, `4e306ce` |

### Latest completed milestone
**"Platform hardening & UAT readiness"** (through `4e306ce`, 30 Jul 2026): seed-data integrity,
Redis rate limiting, App Check, security hardening, and repo reorganisation.

### Point where development stopped
After commit `4e306ce` (2026-07-30 10:53), with **uncommitted work in the working tree**:
1. `public/js/firebase.js` — live reCAPTCHA v3 key swap + `ReCaptchaV3Provider` activation (diff
   shown by `git status`).
2. `public/docs/tenant-guide/` — docs-as-code framework (manifest + template + step 01) —
   **untracked**; manifest lists steps 02/03 with empty `files: []`.

`PROJECT_STATUS.md` (updated 30 Jul) documents the intended next steps (P1 UAT → P2 docs → P3
airline pilot → P4 CAAN pilot → P5 Cloud Run go-live) — none have started.

---

## 6. Feature Status Matrix

Legend: ✅ Fully implemented · 🟡 Partially implemented · ❌ Not implemented
All items cross-checked against source.

| Feature | Status | Evidence | Notes |
|---|---|---|---|
| Firebase Authentication + Login | ✅ | `public/login.html`, `backend/app/routes/auth.py` | Role-based redirect; register/refresh endpoints exist (refresh is a stub). |
| RBAC custom claims (4 roles) | ✅ | `middleware/auth.py:47-167`, `firebase.py:106-116` | Claims + Firestore email fallback + tenant normalization. |
| Firestore rules & tenant isolation | ✅ | `firestore/firestore.rules` | `isOwnTenant()`; CAAN read-only; immutable responses/reports. |
| VSR submission | ✅ | `public/js/vsr.js:349`, `routes/reports.py:95-127` | Anonymous toggle, ICAO taxonomy, background AI. |
| MOR submission | ✅ | `public/js/mor.js:414`, `routes/reports.py:48-93` | ECCAIRS validation, `investigation_status`. |
| Report list / detail | ✅ | `routes/reports.py:129-159`, `public/js/report.js` | ~60-field response. |
| AI classification (Gemini) | ✅ | `services/gemini.py:86-268` | Real model + keyword `mock_analysis` fallback; `classify_mandatory` is keyword-only. |
| ICAO risk assessment lifecycle | 🟡 | `services/risk_matrix.py`, `routes/reports.py:161`, tests | S×P + confirm/override works & tested; **`PUT /risk-matrix` crashes**; configurable thresholds **not used**; reports (5/9/15) vs hazards (3/6/12) threshold mismatch. |
| Hazard register & lifecycle | ✅ | `services/hazard_service.py`, `routes/hazards.py` | Status workflow, assign, auto-create from reports. |
| CAN/CAP workflow | ✅ | `services/can_cap_service.py`, `routes/can_cap.py` | CAN issue, CAP submit/review. |
| Verification & closure | ✅ | `services/verification_service.py`, `routes/verification.py` | Verify, close, reopen. |
| Quarterly/Annual reporting + PDF | ✅ | `services/report_generator.py`, `pdf_generator.py`, `routes/reporting.py` | PDF fallback when reportlab absent (Render). |
| Flight diversions | ✅ | `services/flight_diversion_service.py`, `routes/flight_diversions.py` | Auto-ID, hazard linking. |
| Airline dashboard | ✅ | `services/dashboard_service.py`, `public/safety.html`, `public/js/dashboard.js` | 6 widgets, heat map, KPI cards. |
| CAAN SSP dashboard | 🟡 | `routes/dashboard.py:157-204`, `public/caan.html` | Aggregation works (collectionGroup) but trend/benchmark return placeholder `None`. |
| Admin portal & tenant mgmt | ✅ | `public/admin/index.html`, `routes/admin.py` | Also a duplicate legacy `public/dashboard/index.html`. |
| **Survey (SMS capability)** | 🟡 | `public/survey/default_q.js`, `public/portal/survey/default_q.js`, `seed/surveys.py` | **Charter non-compliant live survey** (custom culture dims, 19 q); portal survey is 23 q / 4 pillars but not 12-element keyed; **no backend survey endpoint**; frontend writes `surveyResponses`, seed writes `surveys`. |
| Seed dataset (930/620/245) | ✅ | `backend/seed/`, `scripts/seed/` | Deterministic, idempotent; migrations run; 2 ISO-string leftovers. |
| 20-airline provisioning | ✅ | `routes/admin.py:163`, `scripts/provision-20-airlines.js`, `docs/ONBOARDING_CREDENTIALS_20_AIRLINES.md` | Hardcoded password. |
| App Check (client) | ✅ | `public/js/firebase.js:163-190` | Live key **uncommitted**; bypass guards for localhost/placeholder. |
| Rate limiting | ✅ | `middleware/rate_limit.py`, `core/security.py` | Redis (Upstash) decorator on 3 routes + global in-memory per-IP; many routes uncovered; `survey_submit`/`dashboard` limits defined but **never attached**. |
| Security headers | ✅ | `core/security.py:11-20`, `firebase.json` headers | HSTS, nosniff, DENY, XSS, referrer, permissions. |
| Metrics / health endpoints | ✅ | `core/metrics.py`, `main.py:134-153` | `/metrics`, `/health`, `/live`, `/ready`. |
| Cloud Functions | ❌ | `functions/` empty | Declared "not required" — all logic in backend API. |
| CI/CD pipeline | ❌ | `.github/workflows/deploy.yml.disabled` | Only disabled Astro Pages workflow; no test job. |
| Cloud Run deployment | ❌ | `backend/cloudrun.yaml` exists | Not deployed; still on Render free tier. |
| Unit/integration tests | ✅ | `backend/tests/` (24 tests) | All pass (verified run). |
| E2E tests | 🟡 | `tests/e2e/` | Target live API; **contradictory** assertions (risk-matrix 403 vs 200); stale `e2e_tokens.json`. |
| Tenant docs-as-code | 🟡 | `public/docs/tenant-guide/` | Step 01 only (untracked); steps 02–03 empty. |

---

## 7. Technical Debt Register (prioritized)

Severity: CRITICAL → HIGH → MEDIUM → LOW. Effort in engineering-days (1 ed ≈ 1 focused day).

### CRITICAL

1. **Hardcoded admin secret gates dangerous unauthenticated endpoints**
   - Where: `backend/app/routes/admin.py:96` `SETUP_SECRET = "aviasafe-e2e-setup-2026"`; used at
     `setup-claims` (104), `provision-airlines` (166), `fix-tenant-ids` (251), `check-data` (280),
     `migrate-seed-data` (310), `create-seed-users` (387), `seed-demo-data` (402).
   - Why it matters: any caller with this (publicly known, in git) string can (a) **escalate any
     user to SUPER_ADMIN**, (b) **wipe & re-seed production Firestore** (`seed-demo-data`,
     `force=True`), (c) **write to the server filesystem** (`migrate-seed-data` rewrites
     `backend/seed/config.py`). Zero Firebase auth on any of them. This invalidates the
     "production-ready" claim and is a critical release blocker.
   - Severity: CRITICAL · Effort: ~0.5 ed · Fix: move secret to env; require SUPER_ADMIN Bearer
     auth (plus setup key as defense-in-depth); disable/remove data-destructive endpoints in prod.

2. **Hardcoded credentials across source and docs**
   - Where: `routes/admin.py:160` (hardcoded password, value redacted); `scripts/provision-20-airlines.js:57`;
      `docs/ONBOARDING_CREDENTIALS_20_AIRLINES.md` (20 passwords); `PROJECT_STATUS.md:322-328`
      (4 test-account passwords, redacted); `DEMO_GUIDE.md` (demo password, redacted); E2E scripts.
   - Why: plaintext shared passwords in version control and static hosting are a credential-leak
     surface; onboarding email instructs users to use a shared default.
   - Severity: CRITICAL · Effort: 1 ed · Fix: env-driven provisioning, force first-login password
     reset, rotate all provisioned credentials, purge from docs/repo.

3. **Open / minimally-guarded debug surface on the live API**
   - Where: `routes/admin.py:277` `/check-data` (no auth, only key); `routes/auth.py:64`
     `/debug-verify` (no auth, no rate limit, returns full decoded token).
   - Why: information disclosure (doc counts, decoded token payload) and an attack primitive.
   - Severity: CRITICAL · Effort: 0.5 ed · Fix: remove from prod or gate behind SUPER_ADMIN auth.

### HIGH

4. **`PUT /risk-matrix` crashes with `TypeError`**
   - Where: `routes/admin.py:86` calls `set_risk_matrix_config(tenant_id, data)` but signature is
     `(tenant_id, config, updated_by)` (`services/risk_matrix.py:89`).
   - Why: this is a headline DEMO feature (DEMO_GUIDE step 2d "Risk Matrix Configuration"); every
     invocation 500s.
   - Severity: HIGH · Effort: <0.5 ed · Fix: pass `updated_by=user["uid"]`.

5. **Configurable risk-matrix thresholds are never used in scoring**
   - Where: `get_risk_level()` defaults to module `THRESHOLDS_DEFAULT` (`risk_matrix.py:61-71`);
     `classify_risk()` uses a different scheme (3/6/12 vs 5/9/15) for hazards
     (`risk_matrix.py:142-150`); stored tenant matrix is only fetched/returned, never plumbed.
   - Why: "Adjust thresholds" does nothing; reports and hazards disagree on the same S×P.
   - Severity: HIGH · Effort: 1–2 ed · Fix: pass stored thresholds into scoring; unify schemes.

6. **Survey does not match the Product Charter (Phase 6A is still open)**
   - Where: live questionnaire `public/survey/default_q.js` uses custom sections A–D (19 q);
     portal questionnaire `public/portal/survey/default_q.js` (23 q, 4 pillars but not the 12
     element IDs); backend seed uses 4 pillars/12 elements (`seed/config.py:6-56`). No survey
     router exists; frontend writes `surveyResponses` (`public/survey/app.js:328`) while seed uses
     `surveys`.
   - Why: core product objective #1 ("measure SMS capability") is delivered by a non-compliant
     questionnaire with no backend path; dashboard pillar aggregation and seed data cannot agree.
   - Severity: HIGH · Effort: 3–5 ed · Fix: single 4-component/12-element questionnaire, backend
     survey endpoint, unified collection + migration.

7. **Fake Firebase keys and mock auth bypasses in `public/portal`**
   - Where: `public/portal/survey/app.js:16-21` and `public/portal/dashboards/dashboard.js:13-20`
     (`AIzaSyFakeKey_ForTestingPhaseOnly2026`); dashboard.js:66-73 email-domain auth bypass;
     caan.js:22-29 fixed demo emails; `portal/dashboards/safety.html:268` "logic will be built in
     the next step".
   - Why: shipping demo/mock code that bypasses auth; portal survey will fail against the real
     project.
   - Severity: HIGH · Effort: 1–2 ed · Fix: delete/replace with the real `public/js` stack.

8. **Contradictory deployment definitions & no CI/CD**
   - Where: root `render.yaml` (bare python) vs `backend/render.yaml` (Docker);
     `.github/workflows/deploy.yml.disabled`; `package.json:13-14` stub build/test.
   - Why: deployment ambiguity and zero automated verification; a new engineer cannot tell which
     Render config is live.
   - Severity: HIGH · Effort: 1–2 ed · Fix: pick one render.yaml; add a real CI workflow (lint +
     pytest) and delete the disabled one.

### MEDIUM

9. **Date-filter fallback masks root cause in repository**
   - `services/repository.py:147-155` retries without date filter when 0 results but raw docs
     exist — hides the string-vs-Timestamp issue rather than fixing it; can return stale data.
   - Effort: 0.5–1 ed · Fix: enforce Timestamp on write; remove fallback.

10. **Deployed indexes (camelCase) mismatch backend snake_case queries**
    - Root `firestore.indexes.json` targets camelCase (`submittedAt`, `reportType`); backend
      `backend/firestore.indexes.json` (snake_case, collectionGroup) is **not referenced** by
      `firebase.json`. Query failures are handled by fallbacks (e.g. dashboard sorts) instead of
      correct indexes.
    - Effort: 1 ed · Fix: reconcile single authoritative index file with actual queries.

11. **E2E suite is contradictory and targets live production**
    - `tests/e2e/e2e_test.py:364` expects risk-matrix 403 for AIRLINE_ADMIN; `e2e_test2.py:304`
      expects 200. `e2e_tokens.json` holds stale mislabeled tokens. Tests write to the live DB.
    - Effort: 1 ed · Fix: converge assertions; run against emulator; refresh tokens.

12. **Unrestricted public VSR/responses create**
    - `firestore/firestore.rules:61-79` allow `create` to anyone with a matching `tenantId` in the
      body — spam/garbage-injection risk for a public API.
    - Effort: 0.5 ed · Fix: App Check enforcement server-side or honeypot/rate-limit; consider
      requiring report `status`.

13. **Legacy dead code & schema drift**
    - `backend/app/database.py` (Supabase stub), orphaned `__pycache__/verify_schema.pyc`, unused
      imports (`auth.py:17`, `admin.py:21,25`, `dashboard.py:18`, `reports.py:22`), dead
      `get_icao_level_from_string`/`get_icao_probability_from_likelihood`
      (`risk_matrix.py:105-139`), stub `refresh` endpoint (`auth.py:114-119`), duplicate
      tenant-admin pages (`public/dashboard/index.html` vs `public/admin/index.html`), unused
      `public/js/app.js`, un-referenced `public/admin/app.js` (redirect contradicts page design).
    - Effort: 0.5–1 ed · Fix: prune; add a lint pass.

14. **Frontend payload/key inconsistencies**
    - `mor.js`/`vsr.js` send `occurrence_date_time`/`occurrence_location` while `report.js` uses
      `occurrence_date`/`location`; `tenant.js` uses uninitialized `db` global
      (`tenant.js:65,85`); `admin` provision writes snake_case `survey_config.open_date` while
      frontend reads camelCase `openDate`; missing `statusBox` element (`login.html:307`).
    - Effort: 1 ed · Fix: single API contract + shared helpers; init Firebase before `tenant.js`.

15. **Seed timestamp leftovers**
    - `risk_matrix_config.updated_at` ISO string (`seed/operators.py:70`), `seed_metadata.seeded_at`
      ISO (`seed/runner.py:157`) — the exact class of bug the `/fix-timestamps` migration removed.
    - Effort: 0.5 ed · Fix: use Firestore Timestamps.

### LOW

16. **Docs drift** — root `README.md` is one heading; `README-sms.md`/`docs/SECURITY.md` describe
    the abandoned Supabase era (PostgreSQL, Netlify, MFA, AES-256). Effort: 1 ed.
17. **Tenant-guide steps 02/03** — manifest files empty (`public/docs/tenant-guide/manifest.json`).
    Effort: 2 ed.
18. **Rate-limit config** — `survey_submit`/`dashboard` limits defined but never attached
    (`middleware/rate_limit.py:41-47`); `ssl_cert_reqs=CERT_NONE` (`rate_limit.py:31`) — weakens
    transport security for Redis. Effort: 0.5 ed.
19. **Caching** — class-level TTL dict, no LRU (`repository.py:64-65`); fine at prototype scale.
    Effort: 1 ed (when scaling).
20. **CAAN placeholder values** — `get_caan_trends`/`get_caan_benchmark`/`get_admin_usage` return
    `None` (`dashboard_service.py:115-142,206-220`). Effort: 1 ed.

---

## 8. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Privilege escalation / data loss via `SETUP_SECRET`** on live API | High (key public in git) | Critical (SUPER_ADMIN claims, DB wipe, filesystem write) | Immediate: env secret + SUPER_ADMIN auth guard; remove destructive endpoints from prod (TD-1). |
| R2 | **Credential exposure** (plaintext passwords in repo + docs + Hosting) | High | High (account takeover of test/seed accounts; onboarding accounts share a password) | Rotate + purge; enforce per-user passwords (TD-2, TD-3). |
| R3 | **Survey data non-compliant with charter** confuses SMS Health metrics | Certain (already true) | Medium-High (product delivers wrong/double source of truth) | Phase 6A refactor to 4 components/12 elements + backend API (TD-6). |
| R4 | **Risk matrix behaves inconsistently** (crash + ignored thresholds) erodes stakeholder trust | High | Medium | Fix admin.py:86; plumb thresholds; unify schemes (TD-4, TD-5). |
| R5 | **Deployment ambiguity / no CI** → environment drift, broken release | Medium | Medium | Single render.yaml; CI with pytest (TD-8). |
| R6 | **Firestore index mismatch** → 500s / fallback stale data at scale | Medium | Medium | Authoritative index file matching queries (TD-10). |
| R7 | **UAT/pilot blocked by known 500s** (risk-matrix) and open debug endpoints | Medium | Medium | Fix before pilot (TD-4, TD-3). |
| R8 | **Public report/responses spam** (unauthenticated create) | Medium | Low-Medium | Server-side App Check / rate limiting (TD-12). |
| R9 | **Gemini API cost/availability** on Render free tier | Medium | Low | mock fallback exists; move AI off-request / to Cloud Run. |
| R10 | **Single maintainer dependency** — docs-in-code + tests mitigate bus factor | Medium | Medium | Continue docs-as-code; CI; onboarding guide. |

---

## 9. Production Readiness Assessment

| Check | Status | Evidence / note |
|---|---|---|
| All core flows implemented | ✅ | Feature Matrix §6 |
| Unit tests green | ✅ | `24 passed` (verified) |
| Security rules enforced | ✅ | `firestore.rules` |
| **AuthN/AuthZ on admin surface** | ❌ | Hardcoded secret; no Firebase auth (TD-1) |
| **Credentials managed** | ❌ | Plaintext in repo/docs (TD-2) |
| **Debug surface closed** | ❌ | `/check-data`, `/debug-verify` open (TD-3) |
| **Known 500s fixed** | ❌ | `PUT /risk-matrix` crashes (TD-4) |
| **Charter-aligned survey** | ❌ | Live survey non-compliant (TD-6) |
| **Configurable risk matrix functional** | ❌ | Thresholds not plumbed (TD-5) |
| CI/CD | ❌ | Disabled workflow only (TD-8) |
| Single deployment definition | ❌ | Two render.yaml (TD-8) |
| Indexes aligned with queries | ❌ | camelCase vs snake_case (TD-10) |
| Secrets externalized | ❌ | `SETUP_SECRET`, passwords hardcoded |
| HTTPS | ✅ | Hosting + Render |
| Observability | 🟡 | Logs + `/metrics` exist; no error alerting |

**Verdict:** The platform is **functionally UAT-capable but not yet safe to release or pilot**.
The critical security items (§7 CRITICAL) must be remediated before external users are onboarded;
Cloud Run go-live additionally requires CI, single deployment config, and index reconciliation.

---

## 10. Last Completed Engineering Task (where development stopped)

**Last committed task:** *Repository hardening & reorganisation batch* — culminating commit
`4e306ce` (2026-07-30): "chore(repo): stop tracking runtime logs". The immediately preceding
functional commits in the same batch:

- `70a96b6` — demote diagnostic logs info→debug (`services/repository.py`,
  `services/dashboard_service.py`)
- `c1fa7f6` — tenant_id normalization, Firestore diagnostics, date-filter fallback
  (`middleware/auth.py`, `services/repository.py`, `services/dashboard_service.py`)
- `c8c252a` — App Check bypass guards for local dev / placeholder keys
- `49d63f9`/`f3cf837` — Replace slowapi with Upstash Redis rate limiting + headers
- `f2790b7` — hardened Firestore rules, App Check, rate limiting, security headers
- `130b5a8`/`2792764`/`f527bb9`/`004fb9a` — seed-data migrations (tenant IDs, timestamps)
- `957e8ce`/`e04884d` — repo reorganisation (E2E/scripts layout; remove node_modules)

**Work in progress at the stop point (uncommitted):**
1. `public/js/firebase.js` — live reCAPTCHA v3 key + `ReCaptchaV3Provider` activation (staged for
   commit but not committed; a secret-bearing change).
2. `public/docs/tenant-guide/` — docs-as-code framework (untracked): `manifest.json`,
   `templates/STEP_DOCUMENTATION_TEMPLATE.md`, `01-getting-started/1.0-overview.md`; steps 02–03
   listed but unwritten.

**Interpretation:** development stopped in the middle of the "UAT prep / App Check activation /
tenant onboarding documentation" effort, after the feature set and hardening were complete but
before: committing the App Check activation, writing tenant-guide steps 02–03, running UAT, and
beginning the airline/CAAN pilots. The next documented steps (`PROJECT_STATUS.md` §12) have not
begun.

---

## 11. Remaining Work

1. **Security remediation** (release-blocker; see §7 CRITICAL/HIGH items 1–3).
2. **Fix known bugs:** `PUT /risk-matrix` TypeError; risk-matrix threshold plumbing; CAAN
   placeholder values.
3. **Phase 6A — Survey charter re-alignment** (4 ICAO components / 12 elements, backend survey
   endpoint, unify `surveyResponses` vs `surveys`, fix snake/camel mismatch).
4. **Engineering hygiene:** remove `public/portal` mock/fake-key code; prune dead code; unify E2E
   assertions; reconcile indexes; single render.yaml.
5. **Release tooling:** active CI (lint + pytest), Cloud Run deployment, real README.
6. **UAT & pilots:** run UAT, fix findings, onboard first airline tenant, then CAAN SSP.
7. **Docs:** tenant-guide steps 02–03; refresh `README-sms.md`/`SECURITY.md` to match Firebase
   stack.

---

## 12. Recommended Next Engineering Task

### Recommendation: Critical Security & Release-Blocker Remediation

**Single best next task** — secure the admin/debug surface and eliminate hardcoded credentials so
the platform can safely proceed to UAT and pilots (the project's own P1–P5). This is the only
correct next step because the current state is *unsafe to expose*, and it unblocks every subsequent
milestone.

**Scope (bounded, ~3–4 engineering-days):**
1. Replace `SETUP_SECRET` hardcoding with an env var (`SETUP_SECRET`) and **require a
   SUPER_ADMIN Bearer token** on all `/api/v1/admin/*` endpoints (defense in depth).
2. Remove or auth-gate `check-data`, `debug-verify`, and the data-destructive
   `seed-demo-data`/`migrate-seed-data` (disable in production via env flag).
3. Remove plaintext credentials from source/docs (provision password → env; rotate seeded users;
   instruct forced password change).
4. Fix `PUT /risk-matrix` (pass `updated_by`) and plumb tenant thresholds into `get_risk_level`
   (unify hazard/report thresholds).
5. Delete/replace `public/portal` mock & fake-key code with the production `public/js` stack.
6. Add pytest regression coverage for the fixed admin endpoints.

**Why this task next:** (a) it is a verified, critical release-blocker; (b) it is bounded and
quick to verify; (c) it precedes UAT/pilots (PROJECT_STATUS.md P1/P3/P4) and Cloud Run go-live
(P5); (d) it is remediation, not feature expansion — consistent with the charter governance rule.

**Dependencies:** requires access to Firebase project + Render env config for secret rotation;
tests run locally with the existing mock stack.

**Risks:** rotating seeded-user passwords breaks the E2E scripts until updated (update
`tests/e2e/*` credentials in the same change); gating admin endpoints may break legit admin flows
— verify with the SUPER_ADMIN UAT account.

**Expected outcome:** a production-safe admin surface, a working risk-matrix config, a clean
credential posture, and a green regression suite — enabling UAT and the airline/CAAN pilots.

**If security is deferred for any reason, the next-best task** is **Phase 6A — Survey Charter
Re-alignment** (TD-6), because it is the charter's explicit "Immediate Work Remaining" and the
core product data source is currently non-compliant.

---

## 13. Prioritized Roadmap

### Immediate (next 1–2 weeks)
1. **P0 — Security remediation** (TD-1, TD-2, TD-3): env secret + auth guard; close debug
   surface; rotate/purge credentials. *(~2–3 ed)*
2. **P0 — Bug fixes** (TD-4, TD-5): `PUT /risk-matrix`, threshold plumbing, unified scoring.
   *(~1–2 ed)*

### Next milestone (2–4 weeks)
3. **P1 — Phase 6A Survey re-alignment** (TD-6): 4 components / 12 elements questionnaire; backend
   survey endpoint; unified collection; migrate `surveyResponses` → `surveys`. *(~3–5 ed)*
4. **P1 — Platform hygiene** (TD-7, TD-13, TD-11): remove `public/portal` mock code, prune dead
   code, reconcile E2E assertions + tokens, single render.yaml. *(~2 ed)*
5. **P1 — Release tooling** (TD-8): real CI (lint + pytest + deploy), authoritative index file
   (TD-10). *(~2 ed)*

### Medium-term (1–2 months)
6. **P2 — UAT** with seed-data validation; fix findings. *(per charter UAT_READINESS.md)*
7. **P2 — Airline pilot** — onboard first airline tenant (20 provisioned, onboarding docs).
8. **P2 — CAAN pilot** — SSP regulatory oversight onboarding.

### Long-term (2–6 months)
9. **P5 — Production go-live:** Cloud Run deployment (`backend/cloudrun.yaml`), custom domain
   `sms.aviasafesystems.com`, Firebase Blaze, remove Render free-tier dependency.
10. **Survey visualization** on airline dashboard (PROJECT_STATUS.md P6) once survey backend
    exists.
11. **Scaling / productization** (ROADMAP.md Phases 4–5): subscription billing, white-label, PWA,
    multi-region, third-party API gateway — **only with explicit charter approval** (governance
    rule).

### Production-readiness checklist (definition of done for go-live)
- [ ] No hardcoded secrets/credentials anywhere in repo or static hosting
- [ ] All admin/debug endpoints require authenticated SUPER_ADMIN
- [ ] `PUT /risk-matrix` works; thresholds used consistently for reports and hazards
- [ ] Survey uses 4 ICAO components / 12 elements with a backend endpoint
- [ ] Green CI (pytest) on every commit; E2E suite converging (no contradictory assertions)
- [ ] Single authoritative `render.yaml` / Cloud Run manifest and index file
- [ ] Rate limiting attached to survey + dashboard endpoints; Redis TLS verified
- [ ] Tenant-guide docs steps 01–03 complete and deployed
- [ ] UAT sign-off + airline/CAAN pilot feedback documented

### Release-readiness checklist
- [ ] Backend on Cloud Run (or stable paid host), env-secrets configured
- [ ] Custom domain + Blaze billing; App Check live key committed from env (not hardcoded)
- [ ] Passwords rotated; onboarding emails instruct forced reset + MFA
- [ ] Monitoring/alerting on `/metrics` + error logs
- [ ] Data backup/export procedure for Firestore
- [ ] Final security review (this report's §7 items all resolved)

---

## 14. Immediate Action Plan (for the recommended next task)

**Task: Critical Security & Release-Blocker Remediation** (est. 3–4 ed)

| Step | Action | Files | Verify |
|---|---|---|---|
| 1 | Add `SETUP_SECRET` (and e.g. `DISABLE_DESTRUCTIVE_ENDPOINTS`) to `core/config.py`; load from env | `backend/app/core/config.py` | `settings.SETUP_SECRET` present |
| 2 | Require SUPER_ADMIN Bearer token on admin endpoints; keep setup key as second factor | `backend/app/routes/admin.py` (all 7 endpoints) | Non-admin call → 403 |
| 3 | Guard/disable `check-data`, `debug-verify`, `seed-demo-data`, `migrate-seed-data` in production | `routes/admin.py:277,306,384,399`, `routes/auth.py:64` | Flag off → 404/403 |
| 4 | Remove plaintext provisioning password; read from env; force password reset on first login | `routes/admin.py:160`, `scripts/provision-20-airlines.js`, docs | No password literals in repo |
| 5 | Rotate seeded-user passwords; update `tests/e2e/*` + status docs accordingly | seed users, E2E scripts | E2E auth passes with new creds |
| 6 | Fix `PUT /risk-matrix`: pass `updated_by=user["uid"]`; plumb stored thresholds into `get_risk_level`/`classify_risk`; add unit tests | `routes/admin.py:86`, `services/risk_matrix.py`, hazard/report services, `backend/tests/` | `pytest` green; matrix update persists & changes risk levels |
| 7 | Replace `public/portal` mock/fake-key code with production stack (or remove) | `public/portal/**` | No fake keys / auth bypasses remain |
| 8 | Run full suite + E2E (against non-destructive paths); update `PROJECT_STATUS.md` | `backend/tests/`, `tests/e2e/`, `PROJECT_STATUS.md` | `24+ passed`; E2E pass |

**Definition of done:** no hardcoded secrets; admin surface authenticated; debug/destructive
endpoints closed in prod; risk-matrix config functional and honored by scoring; regression tests
green; repo ready for UAT kick-off.

---

*End of report. This document is the authoritative baseline for the next development phase.
Next phase begins only after stakeholder approval of this report and the recommended action plan.*

---

## RC-1 Completion Report

**Phase:** RC-1 — Security Hardening & Release Blockers
**Date completed:** 2026-08-02
**Status:** Code + local verification complete. Deployment env-config and credential rotation pending (see "Deployment follow-up").

### Scope delivered
Per §12 action plan: (1) remove hardcoded secrets; (2) authenticate the admin surface with
SUPER_ADMIN; (3) close the debug/destructive surface; (4) remove plaintext credentials from code;
(5) fix the critical `PUT /risk-matrix` release blocker; (6) remove `public/portal` mock/fake-key
code. App Check and Firestore rules were reviewed (see "Remaining issues").

### Files changed

| File | Change |
|---|---|
| `backend/app/core/config.py` | Added env-only settings: `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`, `DEFAULT_SEED_PASSWORD`, `DISABLE_DESTRUCTIVE_ENDPOINTS` (default `True`). |
| `backend/app/routes/admin.py` | Removed hardcoded `SETUP_SECRET = "aviasafe-e2e-setup-2026"` and `STANDARD_PASSWORD`; added `_verify_admin_setup()` (constant-time compare, env secret); all 5 retained admin endpoints now require `get_admin_user` (SUPER_ADMIN Bearer); removed `/check-data` and `/migrate-seed-data`; gated `/seed-demo-data` + `/create-seed-users` behind `DISABLE_DESTRUCTIVE_ENDPOINTS`; fixed `PUT /risk-matrix` `TypeError` by passing `updated_by=user["uid"]`. |
| `backend/app/routes/auth.py` | Removed `/debug-verify` and `DebugVerifyRequest`. |
| `backend/seed/config.py` | `DEMO_USERS` and `OPERATOR_USER_TEMPLATES` passwords now sourced from env (`DEFAULT_SEED_PASSWORD`) — no literals. |
| `backend/seed/users.py` | Operator-profile passwords use `DEMO_USER_PASSWORD`. |
| `scripts/provision-20-airlines.js` | Password read from `DEFAULT_PROVISION_PASSWORD` env; fails fast if unset. |
| `scripts/seed/run_seed.py`, `scripts/seed/check_seed.py` | Require `SUPER_ADMIN_ID_TOKEN` + `SETUP_SECRET` env; call `/seed-demo-data` with Bearer header. |
| `tests/e2e/e2e_setup_claims.py` | Uses `SUPER_ADMIN_ID_TOKEN`/`SETUP_SECRET` env; Bearer header. |
| `tests/e2e/e2e_auth.py`, `e2e_test.py`, `e2e_test2.py`, `e2e_diag.py` | Test-account passwords moved to env (`AVIASAFE_PW_AIRLINE/CAAN/ADMIN/SAFETY`). |
| `tests/e2e/test_dash.py` | Login password from `DEFAULT_SEED_PASSWORD` env. |
| `public/portal/survey/app.js`, `public/portal/dashboards/dashboard.js` | Replaced fake config with real Firebase config; removed email-domain auth bypass in `dashboard.js`. |
| `public/portal/dashboards/caan.js` | Replaced mock auth with real Firebase Auth (`signInWithEmailAndPassword` + `onAuthStateChanged`). |

### Security fixes completed
1. **No setup secret grants access.** The admin setup key is now loaded from the environment
   (`SETUP_SECRET`) and is only a *second factor* — a SUPER_ADMIN Firebase ID token is mandatory on
   every admin endpoint. Wrong key → 403; server secret unset → 503 (fail closed).
2. **Debug/destructive surface closed.** `/check-data`, `/debug-verify`, and `/migrate-seed-data`
   removed entirely (404). `/seed-demo-data` and `/create-seed-users` return 404 by default
   (`DISABLE_DESTRUCTIVE_ENDPOINTS=True`); `/migrate-seed-data`'s server-filesystem write is gone.
3. **Plaintext credentials purged from code.** The legacy demo password (redacted), the legacy
   provisioning password (redacted), the four RC-1 test-account passwords (redacted),
   `AIzaSyFakeKey…`, and `aviasafe-e2e-setup-2026` literals remain **nowhere** in the repo (verified
   by grep at RC-1; RC-3 additionally purged them from documentation).
4. **`PUT /risk-matrix` no longer 500s.** `set_risk_matrix_config(tenant_id, data, updated_by=user["uid"])`
   matches the service signature (§7 TD-4).

### Verification
- `pytest backend/tests/` → **24 passed** (0 failed; no regressions).
- Route-surface check (app import): `/api/v1/admin/{setup-claims, provision-airlines, fix-tenant-ids,
  risk-matrix, seed-demo-data, create-seed-users}`; `/check-data`, `/debug-verify`, `/migrate-seed-data` → **404**.
- Auth-gating check (TestClient, mocked `verify_firebase_token`):
  - no token → **403**; AIRLINE_ADMIN on `/setup-claims` → **403** (SUPER_ADMIN required)
  - SUPER_ADMIN + wrong setup key → **403**; server secret unset → **503**
  - GET `/risk-matrix` as AIRLINE_ADMIN → **200** (safety-manager auth unchanged)
  - `/seed-demo-data` with `DISABLE_DESTRUCTIVE_ENDPOINTS=True` → **404**
- End-to-end hitting of guarded endpoints against live Render requires Firebase credentials/tokens
  and is documented as the E2E path (env-driven now).

### Remaining issues (deferred / out of RC-1 scope)
1. **Deployed-env configuration** (operator action): set `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`,
   `DEFAULT_SEED_PASSWORD` in Render env; keep `DISABLE_DESTRUCTIVE_ENDPOINTS=True` in production.
2. **Credential rotation for existing users**: seed/provisioned user passwords must be rotated and a
   forced first-login reset issued (docs `DEMO_GUIDE.md`, `ONBOARDING_CREDENTIALS_20_AIRLINES.md`,
   `WELCOME_EMAIL_20_AIRLINES.md`, `UAT_READINESS.md` still carry the shared defaults).
3. **App Check** (reviewed): client activation present (`public/js/firebase.js`, live reCAPTCHA site
   key). Backend does not yet enforce the `X-Firebase-AppCheck` token server-side — recommended before
   public launch.
4. **Firestore rules** (reviewed): match the RBAC model; `allow create` for public
   `responses`/`reports`/`public_responses` remains an unauthenticated spam surface (§7 TD-12, MEDIUM).
5. **Risk-matrix thresholds not plumbed** into `get_risk_level`/`classify_risk` (§7 TD-5, HIGH —
   functional improvement, not a crash).
6. **Docs drift**: status tables in `PROJECT_STATUS.md`/this report still describe the removed
   endpoints as current; status docs need a follow-up refresh.

### Known risks
- Admin/setup endpoints return **503** until `SETUP_SECRET` is configured — intentional fail-closed.
- Seeding/provisioning now requires env secrets + `DISABLE_DESTRUCTIVE_ENDPOINTS=False`; scripts
  `scripts/seed/*`, `tests/e2e/*` exit with a clear message when env vars are absent.
- `public/js/firebase.js` live reCAPTCHA site key (pre-RC-1 WIP) is still uncommitted.

### Deployment follow-up (required before UAT/pilot)
- Add `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`, `DEFAULT_SEED_PASSWORD` to Render env.
- Redeploy; smoke-test the 401/403/404/503 paths above against the live API.
- Rotate provisioned/seed passwords; reissue onboarding credentials; update docs.
- Decide on server-side App Check enforcement and the public-create spam control (TD-12).

**RC-2 (not started):** per phase governance, no further phase begins without approval.

---

## RC-2 Completion Report

**Phase:** RC-2 — Functional Corrections & Regression Validation (Risk Matrix Consistency)
**Date completed:** 2026-08-02
**Status:** Code + local verification complete. Live-fire validation against Render remains the
deployment follow-up (documented in "Regression results"). **READY FOR RC-3.**

### 1. Executive Summary

RC-2 delivered the Risk-Matrix consistency corrections (TD-5) and full regression validation.

**Defect fixed (§7 TD-5, HIGH):** hazard risk classification used a hardcoded 3/6/12 threshold
scheme (`classify_risk`) while reports/dashboards/gemini/seed used the canonical configurable
5/9/15 scheme (`get_risk_level`) — so the *same Severity × Probability* produced *different* risk
levels depending on the surface, and admin-adjusted thresholds had no effect on scoring.

**Fix:** one canonical, configurable classification is now used everywhere. `classify_risk` is an
alias of `get_risk_level`; `risk_outcome` uses the same matrix boundaries; stored per-tenant
thresholds are plumbed into all scoring (reports, hazards, AI-suggested assessment) via a new
`get_thresholds(tenant_id)` helper; the duplicate seed threshold logic was removed; the frontend
hazard pages now match the canonical 5/9/15 matrix; `risk_matrix_config.updated_at` is stored as a
Firestore Timestamp (TD-15 for this document).

### 2. Files Modified

| File | Change |
|---|---|
| `backend/app/services/risk_matrix.py` | `get_risk_level` robust to empty thresholds; new `get_thresholds(tenant_id)` (stored config → defaults fallback); `classify_risk` now delegates to `get_risk_level` (unified scheme); `risk_outcome` uses matrix boundaries + `compute_risk_index`; removed dead `get_icao_level_from_string`/`get_icao_probability_from_likelihood` (TD-13); `set_risk_matrix_config` stores `updated_at` as Timestamp. |
| `backend/app/services/hazard_service.py` | Uses `compute_risk_index` (not inline product); passes `get_thresholds(self.tenant_id)` into `classify_risk`/`risk_outcome` on create and update. |
| `backend/app/services/report_service.py` | Plumbs `get_thresholds(self.tenant_id)` into `get_risk_level` in `create_report`, `run_ai_analysis` (AI-suggested), `confirm_risk_assessment`. |
| `backend/app/routes/reports.py` | Dropped unused `classify_risk` import; `_determine_hazard_priority` uses `compute_risk_index`. |
| `backend/seed/generator.py` | Removed duplicate `RISK_THRESHOLDS` + `get_risk_level_from_index`; uses app-service `compute_risk_index`/`get_risk_level`. |
| `backend/seed/reports.py` | Uses app-service `compute_risk_index`/`get_risk_level`. |
| `backend/seed/operators.py` | `risk_matrix_config.updated_at` stored as Timestamp (datetime), not ISO string. |
| `public/js/hazards.js` | `classifyHazardRisk`/`getRiskOutcome` use canonical 5/9/15 (matches `dashboard-utils.js` `ICAO_THRESHOLDS`); used by `public/hazards/create.html` preview. |
| `backend/tests/test_risk_matrix.py` | **New** — 16 focused tests (pure functions + hazard/report service classification + threshold plumbing). |

### 3. Functional Issues Corrected

1. **Hazards and reports disagreed on the same S×P** (TD-5 root cause). Under the old scheme
   S=3/P=3 (index 9) → hazard "High"/"Intolerable" but report "Medium"/"Tolerable". Now both use
   the canonical configurable matrix: index 9 → **Medium**/Tolerable. `classify_risk` is identical
   to `get_risk_level` for every index 1–25 (verified by test).
2. **Admin "adjust thresholds" had no effect.** Stored `metadata/risk_matrix` thresholds are now
   read by `get_thresholds(tenant_id)` and applied to report scoring, hazard classification and
   risk outcome. Custom low/med/high boundaries are honoured (verified by tests with a 3/6/12
   tenant config).
3. **Frontend hazard preview diverged.** `hazards.js` `classifyHazardRisk`/`getRiskOutcome` moved
   from 3/6/12 to the canonical 5/9/15 so the hazard create/preview page agrees with the backend,
   reports and dashboards.
4. **Risk outcome boundaries aligned.** `risk_outcome` (Acceptable/Tolerable/Intolerable) now maps
   to the same matrix (Acceptable ≤ low_max, Tolerable ≤ medium_max, else Intolerable), matching the
   platform's own `RISK_LEVEL_LABELS_DEFAULT` (Low=Acceptable, Medium=Tolerable, High/Very
   High=Intolerable). Labels unchanged.
5. **Duplicate risk logic removed.** Seed's private `RISK_THRESHOLDS`/`get_risk_level_from_index`
   replaced by the canonical app-service functions (seed already produced 5/9/15 values, so seeded
   data is unchanged).
6. **Dead code / hygiene (TD-13, scoped).** Removed unused `classify_risk` import in
   `routes/reports.py` and the dead `get_icao_level_from_string`/`get_icao_probability_from_likelihood`.
7. **Firestore timestamp (TD-15, risk-matrix doc).** `risk_matrix_config.updated_at` written by the
   seed and by `PUT /risk-matrix` is now a Timestamp, not an ISO string.

### 4. Regression Results

| Area | Result |
|---|---|
| AuthN / AuthZ | PASS — RBAC checks (USER→403; AIRLINE_ADMIN/CAAN_SMD/SUPER_ADMIN flows) unchanged and green in `test_risk_assessment_lifecycle.py`. |
| VSR submission + auto risk calc | PASS — risk_index/risk_level assertions unchanged (index 1/9/25 → Low/Medium/Very High). |
| MOR submission + auto risk calc | PASS — same canonical scoring, green. |
| Risk Assessment confirm (official) | PASS — 2×3→Medium, 4×4→Very High, 5×3→High, 2×5→High confirmations unchanged; stored thresholds now applied. |
| Risk Matrix config | PASS — GET/PUT `/risk-matrix` unchanged; stored thresholds now honoured by scoring (new tests). |
| Dashboards / metrics | PASS — `test_metrics_service.py` green (risk_score 0–1 concept untouched). |
| Reporting | PASS — report create/retrieve/confirm lifecycle green. |
| Notifications | N/A — no notification service implemented. |
| Firestore interactions | PASS — mocked in-memory Firestore suite green (40 tests). |
| Admin portal | PASS — RC-1 auth-gating unchanged; risk-matrix endpoints verified. |
| Seed package | PASS — `seed.generator/reports/operators` import cleanly; seeded risk values unchanged (seed already used 5/9/15). |
| App import / route surface | PASS — `app.main` imports (153 routes); no import regressions. |
| Frontend syntax | PASS — `node --check` on `hazards.js`. |

**RC-1 regression check:** all RC-1 changes (admin auth-gating, env secrets, removed debug
endpoints, portal auth) are untouched by RC-2 and remain covered by the passing suite.

### 5. Test Results

`python -m pytest backend/tests/ -q` → **40 passed, 0 failed** (baseline 24 + 16 new in
`test_risk_matrix.py`). No regressions.

### 6. Remaining Technical Debt

1. **Gemini prompt lists default thresholds** (`gemini.py:79-82`) — informational text for the LLM
   only; the authoritative AI-suggested `risk_level` is recomputed server-side with stored tenant
   thresholds in `report_service.run_ai_analysis`. No action required for consistency.
2. **`risk_score` (0–1) vs `risk_index` (1–25)** remain two distinct concepts (dashboard KPIs use
   the 0–1 score; risk matrix uses the 1–25 product). Intentionally not merged — merging would
   change user-visible behavior.
3. **Legacy Firestore hazards** stored under the old 3/6/12 scheme keep their historical
   `risk_level`/`risk_outcome` values; no migration was performed. New/updated hazards use the
   canonical matrix. A one-off reclassification job could be added later if required.
4. **Other TD-15 leftovers** (`seed_metadata.seeded_at` ISO, etc.) are out of risk-matrix scope.
5. **Live-fire verification** against Render (custom thresholds via `PUT /risk-matrix` then
   re-scoring a report/hazard) is a deployment follow-up requiring a live token.

### 7. Newly Discovered Issues

1. `risk_outcome` boundaries (3/6) were a second, hidden divergence inside `hazard_service` that
   would have disagreed with any report-side risk level after the main scheme was unified — now
   aligned to the matrix (see §3.4). No separate issue remains open.
2. Hazard **priority** (H/M/L, thresholds 6/12 in `_determine_hazard_priority`) is a distinct
   dimension from risk level and is intentionally not governed by the configurable matrix; noted to
   avoid future confusion. No defect found.

### 8. Recommendation

**READY FOR RC-3.** The risk matrix now behaves identically across backend, frontend, seeded
Firestore data, reports, dashboards and hazards, and admin-configured thresholds take effect in
scoring. Before RC-3, the operator must (a) deploy and set env secrets (from RC-1), and (b)
optionally run a live smoke test of `PUT /risk-matrix` with custom thresholds against a
non-production tenant. The next-highest-priority outstanding item remains Phase 6A survey
re-alignment (TD-6).

**RC-3 (not started):** per phase governance, no further phase begins without approval.

---

## RC-3 Completion Report

**Date:** 2 August 2026
**Phase:** RC-3 — Documentation & Operational Readiness
**Outcome:** **READY FOR RC-4**

### 1. Documents Updated

| Document | What changed |
|---|---|
| `README.md` | Replaced a one-line placeholder ("Deployment Synchronization Sync") with a full project README: overview, data sources/audiences, tech stack, repository structure, documentation index, quick start, governance. |
| `ROADMAP.md` | Removed obsolete Supabase/Netlify-era roadmap; rewritten around the actual milestone and RC-phase reality with a charter-gated product backlog. |
| `DEMO_GUIDE.md` | Purged all plaintext passwords (now env-driven `<seed-password>`); corrected seed command to `python -m seed.runner`; added local-setup pointer. |
| `PROJECT_STATUS.md` | Corrected stale repository state (HEAD, debug-endpoint status, route inventory 143→73 v1 business/~153 total), test suite (3+7+14+16 = 40), known-issues, next steps; removed plaintext test passwords. |
| `docs/SECURITY.md` | Full rewrite to the **actual** model (Firebase Auth, custom-claim RBAC, App Check client-side, Firestore rules table, env-driven secrets, fail-closed admin); explicitly corrected outdated Supabase-era claims (MFA required, AES-256, RLS). |
| `docs/UAT_READINESS.md` | Marked superseded by RC phases; corrected route counts; purged plaintext passwords; kept UAT scenario sets. |
| `docs/ONBOARDING_CREDENTIALS_20_AIRLINES.md` | Rewritten from 20 password-bearing tables into a credential-free tenant reference (env-driven provisioning policy). |
| `docs/WELCOME_EMAIL_20_AIRLINES.md` | Removed the shared plaintext password from the email template. |
| `docs/HAZARD_TAXONOMY.md` | Risk levels now **Low \| Medium \| High \| Very High** with the canonical matrix (5/9/15) and tenant-configurability note. |
| `tests/README.md` | Expanded: full unit/integration test matrix (40 tests), risk-matrix mocking note, regression policy, E2E runbook, known test gaps. |
| `design/risk-assessment-v1.md` | Added implementation-status header (spec implemented; "Extreme" bucket corrected to canonical 4-level classification). |
| `PROJECT_STATUS_REPORT_02AUG2026.md` | Added `## Current Status` summary block at top; redacted historical plaintext credential values. |
| `public/docs/tenant-guide/manifest.json` | Steps 02 and 03 now reference authored files (resolves TD-17); `last_updated` bumped. |

### 2. Documents Created

| Document | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | System overview, stack, backend/middleware/route structure, data model, risk matrix, frontend, design patterns. |
| `docs/INSTALLATION.md` | Prerequisites, `backend/.env` setup (full env-var table), local run, seed (`python -m seed.runner`), frontend serve, tests, troubleshooting. |
| `docs/DEPLOYMENT.md` | Current deployment, env vars, Render (Docker) + bare-python, Cloud Run (target), Firebase Hosting, Firestore rules/indexes, rollback, release procedure, environments. |
| `docs/OPERATIONS.md` | Roles, user/tenant management, provisioning, monitoring (`/health`,`/live`,`/ready`,`/metrics`), rate limiting, backup/DR (honest current state), playbook. |
| `docs/ADMIN_GUIDE.md` | Role capabilities, admin API table (setup-key requirements), risk-matrix/tenant config, security responsibilities, checklist, troubleshooting. |
| `docs/API.md` | Verified route inventory (73 canonical v1 business endpoints + legacy aliases + system), auth, conventions, request example, error codes. |
| `docs/KNOWN_LIMITATIONS.md` | Full TD register (TD-1…TD-17 with status), security/operational/functional limitations, planned work. |
| `backend/.env.example` | Safe, commented environment template (no real values). |
| `public/docs/tenant-guide/02-account-setup/1.0-account-profile-setup.md` | Tenant step 02 (role/tenant verification, password policy, RBAC boundaries) per the existing template. |
| `public/docs/tenant-guide/03-safety-reporting/1.0-vsr-mor-submission.md` | Tenant step 03 (VSR/MOR submission, ICAO matrix, AI-suggestion vs official assessment) per the template. |

**Removed:** `README-sms.md` (obsolete "Safety-Health" Supabase/Netlify-era document that conflicted
with the current implementation).

### 3. Documentation Coverage Assessment

| # | Required area | Status | Where |
|---|---|---|---|
| 1 | Project Overview (architecture, stack, repo structure) | ✅ Complete | `README.md`, `docs/ARCHITECTURE.md` |
| 2 | Installation & Local Development | ✅ Complete | `docs/INSTALLATION.md`, `backend/.env.example` |
| 3 | Deployment Guide (Render, Hosting, Cloud Run future, Firestore, env, rollback) | ✅ Complete | `docs/DEPLOYMENT.md` |
| 4 | Operations Manual | ✅ Complete | `docs/OPERATIONS.md` |
| 5 | Administrator Guide | ✅ Complete | `docs/ADMIN_GUIDE.md` |
| 6 | Tenant Guide | ✅ Complete (all 3 steps) | `public/docs/tenant-guide/` (TD-17 resolved) |
| 7 | API Documentation | ✅ Complete (verified inventory) | `docs/API.md` |
| 8 | Security Documentation | ✅ Complete (rewritten to reality) | `docs/SECURITY.md` |
| 9 | Testing Documentation | ✅ Complete | `tests/README.md` |
| 10 | Known Limitations | ✅ Complete | `docs/KNOWN_LIMITATIONS.md` |

**Quality review:** obsolete/conflicting docs removed or rewritten; stale route/version counts
corrected against the running app; all plaintext credentials removed (grep-verified, 0 matches);
all relative links resolve (`ALL LINKS OK`); `manifest.json` parses; full pytest suite green.

### 4. Outstanding Documentation Gaps

1. **No live-fire Cloud Run runbook** — Cloud Run is target-only; the migration runbook is written
   but not yet exercised against a deployed Cloud Run service.
2. **Backup/DR runbook depends on operator action** — Firestore Backups/PITR are not enabled; the
   ops guide documents the procedure but no backup exists yet.
3. **No dedicated staging environment** documented — staging shares the production Firestore.
4. **Tenant-guide is text-only** (no screenshots) — optional polish for the pilot phase.
5. **`UAT_READINESS.md` sign-off table unfilled** — awaiting named UAT participants.
6. **`docs/API.md` is hand-maintained** (verified against OpenAPI at RC-3); no CI regeneration.
7. **`backend/.env.example` not yet consumed by the app** — the backend loads `backend/.env` only;
   the template is an onboarding aid.

### 5. Remaining Technical Debt

Carried from [docs/KNOWN_LIMITATIONS.md](./docs/KNOWN_LIMITATIONS.md): TD-6 (survey re-alignment to
4 components / 12 elements — the highest-priority outstanding item), TD-7 (portal mock code),
TD-8 (no CI/CD; two `render.yaml`), TD-10 (index camelCase/snake_case drift), TD-11/TD-13
(dead-code leftovers), TD-12 (server-side App Check / public-create spam control). Operational:
no automated Firestore backups/PITR; MFA not enforced; no structured audit trail; no PII retention
policy.

### 6. Operational Readiness Assessment

| Criterion | Status |
|---|---|
| Documentation covers all 10 mandated areas | ✅ |
| Test suite green (40 passed) | ✅ |
| Route inventory matches running app (73 v1 business + legacy + system) | ✅ |
| No plaintext credentials anywhere in repo/docs (grep-verified) | ✅ |
| All internal doc links resolve | ✅ |
| Tenant-guide steps 01–03 complete + manifest valid | ✅ |
| Deployment state unchanged and documented | ✅ |
| Operator-facing runbooks (provisioning, monitoring, backups, rollback) | ✅ (written; backups pending enablement) |

**Not yet operationally ready:** automated backups (operator must enable Firestore Backups/PITR),
server-side App Check enforcement, and a dedicated staging environment. These are RC-5/RC-6 items
and do not block RC-4.

### 7. Recommendation

**READY FOR RC-4.** The documentation suite is complete, consistent with the implemented system
(as of RC-2), and free of credential leaks. RC-4 should focus on the charter's explicit
"Immediate Work Remaining": **Phase 6A survey re-alignment to 4 components / 12 elements with a
backend API (TD-6)**. Recommended pre-RC-4 operator actions: (a) review the rewritten `README.md`
and `docs/SECURITY.md`, and (b) enable Firestore Backups/PITR for `gap-analysis-ssp`.

**RC-4 (not started):** per phase governance, RC-4 begins only upon approval.

---

## RC-4 Completion Report

**Date:** 2 August 2026
**Phase:** RC-4 — UAT Readiness (Independent UAT / IV&V execution)
**Outcome:** **READY FOR RC-5 — PILOT DEPLOYMENT** *(conditional on re-deploy of the current repository build — UAT-005)*

### 1. Executive Summary

RC-4 executed UAT as an independent IV&V exercise across all 12 UAT areas, combining static review
of the repository, the automated regression suite, and non-destructive dynamic probes of the live
deployment (`aviasafe-unified-platform.onrender.com`). The core architecture (Firebase ID-token
auth, claim-based RBAC, tenant-scoped Firestore, canonical ICAO 5×5 risk matrix, CAN/CAP +
verification/closure workflow) is sound and the RC-1→RC-3 regression baseline was green.

12 verified findings were recorded (`UAT_DEFECT_REGISTER.md`, UAT-001…UAT-012). **8 were fixed and
verified during this phase**, including Critical/High authorization and cross-tenant defects
(UAT-001 confirm-risk cross-tenant, UAT-002 CAAN CAP reads, UAT-003 reporting tenant override,
UAT-004 survey schema mismatch, UAT-007 cross-tenant write guards, UAT-008 test-integrity masking),
one environment fix (UAT-006 reportlab), and one test-infrastructure fix (UAT-008). The remaining
items are deployment (UAT-005 — live build predates admin auth hardening), recommendations
(UAT-009/010/011), and one deferred data-integrity item (UAT-012).

Final regression: **46/46 passed** (40 baseline + 6 new cross-tenant/authorization tests).
Recommendation: **READY FOR RC-5** once the live backend is re-deployed from the current repository
(admin endpoints currently lack bearer auth on the running build).

### 2. UAT Execution

- **Scenarios:** all 12 UAT areas executed (Authentication, Authorization, Survey, VSR/MOR,
  Hazard Register, Risk Matrix, CAN/CAP, Reporting, Administration, Data Integrity, Performance,
  Security Verification).
- **Regression baseline:** `python -m pytest tests/ -q` → 40/40 passed (pre-fix).
- **Final regression:** 46/46 passed (40 + 6 new cross-tenant/authorization regression tests).
- **Live probes (non-destructive):** `/health`/`/ready`/`/live` healthy; protected endpoints 403;
  `/docs`+`/openapi.json` exposed; unauthenticated POST to admin provisioning paths reached the
  setup-key check (proves auth not enforced on live build — UAT-005).
- **Full report:** `UAT_EXECUTION_REPORT.md` (12 mandated sections). Defect detail in
  `UAT_DEFECT_REGISTER.md`.

### 3. Defects Fixed & Verified

| ID | Severity | Fix |
|----|----------|-----|
| UAT-001 | Critical | `confirm_risk_assessment` now resolves cross-tenant via collection-group `__name__` lookup and updates through the document reference (CAAN/SUPER_ADMIN have no tenant claim); thresholds read from the report's own tenant. |
| UAT-002 | High | CAN/CAP cross-tenant reads (`list_caps`, `latest_cap`, stats) use `doc.reference.collection("caps")`; CAP-list endpoint `response_model=List[dict]` (previously 500 ResponseValidationError). |
| UAT-003 | High | Reporting `tenant_id` override restricted to `CROSS_TENANT_ROLES`; USER without own tenant rejected 403. |
| UAT-004 | High | Survey client now sends `tenantId`; Firestore rule accepts `airline_id` OR `tenantId` (unblocked anonymous submissions). |
| UAT-006 | Medium | `reportlab==4.1.0` added to `requirements.txt`; valid `%PDF-1.4` output verified locally. |
| UAT-007 | High | Tenant-required 403 guards added to CAN/CAP/verification/closure/diversion-link writes (previously wrote to phantom `document(None)` tenants). |
| UAT-008 | Medium | Test claims model production (CAAN/SUPER_ADMIN no tenant); collection-group mock traverses tenant data; collection `get()` returns snapshots — masking eliminated. |

### 4. Defects Verified, No Code Change

| ID | Severity | Action |
|----|----------|--------|
| UAT-005 | Critical | Live deployment runs a pre-hardening build (admin endpoints answer setup-key check without a bearer token; OpenAPI shows `security: null`). Repo code is already correct (`Depends(get_admin_user)` on all admin endpoints). **Re-deploy required.** |
| UAT-009 | Low | Public `/docs` + `/openapi.json` on live — recommendation: `docs_url=None` in production. |
| UAT-010 | Low | `getCurrentUser()` silent 5s timeout resolves null — recommendation: explicit signed-out handling. |
| UAT-011 | Low | `/login.html?tenant=` unused off the deployment host — recommendation: handle/error explicitly. |
| UAT-012 | Medium | Closure gate uses `verifications[-1]` without ordering — deferred; recommend sort by `created_at` DESC. |

### 5. Regression Results

- Pre-fix baseline: 40/40. Post-fix: **46/46 passed** (no regressions).
- New regression tests: CAAN cross-tenant risk confirmation lands in owner tenant; CAAN reads
  CAN/CAP across tenants; CAAN CAN write denied without tenant; USER blocked from other-tenant
  reports; AIRLINE_ADMIN own-tenant report generation; CAAN national report generation.
- Full regression matrix recorded in `UAT_EXECUTION_REPORT.md` §4–§5.

### 6. Remaining Issues / Action Items Before RC-5

1. **Re-deploy the backend from the current repository state** to close UAT-005; verify with a
   no-token probe that admin endpoints return 401/403 and that OpenAPI shows
   `security: [{"HTTPBearer": []}]`.
2. **Documented limitations carried forward:** TD-12 server-side App Check / survey anti-abuse;
   SECURITY.md App Check claim vs rules (no attestation condition) — documentation gap noted.
3. **Recommendations (non-blocking):** UAT-009/010/011; UAT-012 scheduled next release.
4. **Optional:** refresh `docs/API.md` route inventory to reflect the CAP-list `List[dict]` change.

### 7. Recommendation

**READY FOR RC-5 — PILOT DEPLOYMENT**, conditional on completing Action Item 1 (re-deploy to close
UAT-005). All Critical/High defects present in the repository were corrected and verified, and the
remaining findings are deployment actions, documented limitations, or low-severity
recommendations. RC-5 (Pilot Preparation) may begin only after the re-deploy and its verification
are complete, per phase governance.

**RC-5 (not started):** per phase governance, RC-5 begins only upon approval of this report and
completion of the UAT-005 re-deploy.

---

## RC-5 Completion Report

**Date:** 2 August 2026
**Phase:** RC-5 — Operational Pilot Readiness
**Outcome:** **READY FOR RC-6 – PRODUCTION READINESS REVIEW** *(conditional upon successful Render
deployment of the RC-5 candidate — see Pending Operator Actions)*

### 1. Executive Summary

RC-5 prepared the platform for its first operational pilot and validated the deployable artifact.
Because the Render re-deploy requires operator credentials, the live deployment action is treated as
an **external operational dependency** and is recorded as a Pending Operator Action; every other
RC-5 objective was completed.

**Deployment Status (three states, explicitly distinguished):**
- **Repository state — validated.** All RC-1→RC-5 changes are present in the working tree (46 files
  modified vs `4e306ce`). No live secrets in code (grep clean). `pytest` → **46/46 passed**.
- **Local deployment validation — passed.** Docker image built from the working tree
  (`backend/Dockerfile`, python:3.11); container boots and serves; `/health`/`/live`/`/ready`
  respond; protected and admin endpoints return **403 before body validation**; OpenAPI shows all
  admin POST endpoints with `security: [{"HTTPBearer":[]}]`; legacy `/check-data` and
  `/migrate-seed-data` paths are **absent**; reportlab 4.1.0 generates valid `%PDF-1.4`. This proves
  the RC-5 candidate contains the UAT-005 fix.
- **Live production state — pending operator action.** The running Render build is the **pre-RC-1
  hardening build**: admin POST endpoints report `security: null` in the live OpenAPI and legacy
  `/check-data` + `/migrate-seed-data` remain live. UAT-005 is therefore still open on live and the
  re-deploy is required before the pilot begins.

### 2. Deployment Status

| Surface | State |
|---|---|
| Backend Render deploy (UAT-005) | **PENDING** — operator action; live still runs pre-hardening build |
| Frontend Firebase Hosting | Live (`gap-analysis-ssp.web.app`); firebase CLI authenticated for operator deploy |
| Firestore rules / indexes | In repo (validated); deploy pending operator |
| Cloud Run | Target-only (not deployed) |
| Artifact validation | DONE — image builds, boots, auth-enforced, PDF valid, 46/46 tests |

### 3. Smoke Test Results

- **Local (RC-5 candidate container):** `/health` 200 (firebase `unavailable` — expected: local
  `.env` uses a placeholder service key; real key lives in Render env), `/live` 200, `/ready` 200,
  `GET /api/v1/reports` (no token) → 403, `POST /api/v1/admin/setup-claims` (no token, empty body)
  → 403 `Not authenticated` (before body validation) — confirms bearer enforcement.
- **Live (current pre-deploy build):** `/health` 200 firebase connected, `/live` 200, `/ready` 200,
  invalid token `/api/v1/auth/verify` → 401, protected surfaces (reports/dashboard/hazards/cans/
  flight-diversions/metrics) → 403, `/docs` exposed 200, `/api/v1/surveys` → 404. Admin POST
  `security: null` + legacy paths present → **UAT-005 not yet resolved on live**.
- **Regression:** `python -m pytest tests/ -q` → **46 passed** (no regressions).

### 4. Operational Readiness

- Documentation is complete (OPERATIONS, DEPLOYMENT, ADMIN_GUIDE, API, KNOWN_LIMITATIONS, tenant
  guide steps 01–03, onboarding reference). 
- Gaps documented: provisioning curl example in OPERATIONS.md is stale (header/body mismatch);
  no explicit incident-response runbook; no formal support/escalation contact; no dedicated staging
  environment; no automated backups/PITR; server-side App Check not enforced (TD-12); survey
  charter-alignment pending (TD-6); self-registration accepts arbitrary `tenant_id` (pilot risk).

### 5. Outstanding Risks

| # | Risk | Severity | Status |
|---|---|---|---|
| R-A | Live backend runs pre-hardening build (admin endpoints unauth'd) | Critical | Open until operator re-deploys (UAT-005) |
| R-B | No automated Firestore backups / PITR | High | Open; operator action to enable |
| R-C | Public-create spam surface (responses/reports) — no server-side App Check | Medium-High | Open (TD-12) |
| R-D | Self-registration allows self-assigned `tenant_id` (AIRLINE_ADMIN) | Medium | Open; mitigation: disable self-registration or validate during pilot |
| R-E | Survey not charter-compliant (TD-6) | Medium | Open (documented) |
| R-F | `/docs` exposed in production (UAT-009) | Low | Open (recommendation) |
| R-G | DEBUG flag must be false in production env | Low-Medium | Open (operator to confirm on Render) |

### 6. Remaining Technical Debt

Carried: TD-6 (survey), TD-7 (portal mock code), TD-8 (no CI/CD, two render.yaml, service-name
mismatch), TD-10 (index camelCase/snake_case drift), TD-12 (server-side App Check / public-create
spam), TD-15 (`seeded_at` ISO leftover). New: self-registration tenant validation; stale
OPERATIONS.md provisioning example; Redis `ssl_cert_reqs=CERT_NONE` (TD-18); `survey_submit`/
`dashboard` rate-limit definitions never attached.

### 7. Recommendation

**READY FOR RC-6 – PRODUCTION READINESS REVIEW (Conditional upon successful Render deployment).**
RC-5 is complete except for the operator-performed deployment. Once the Pending Operator Actions
below are completed, the pilot may begin. RC-6 begins only upon approval and completion of the
deployment.

### Pending Operator Actions

1. **Trigger the Render deployment using the RC-5 release candidate** (working-tree state at commit
   `4e306ce` + RC-1→RC-5 changes; Docker path `backend/Dockerfile`, service `aviasafe-unified-platform`).
2. **Set/confirm Render env vars:** `SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`,
   `DEFAULT_SEED_PASSWORD`, `DEBUG=false`, `DISABLE_DESTRUCTIVE_ENDPOINTS=true`, `ALLOWED_ORIGINS`
   (incl. `https://gap-analysis-ssp.web.app`), `REDIS_URL`, Firebase/Gemini credentials.
3. **Verify the deployment completed successfully** — confirm live OpenAPI shows
   `security: [{"HTTPBearer":[]}]` on all admin POST endpoints and legacy `/check-data`,
   `/migrate-seed-data` are absent.
4. **Execute production smoke tests against the live environment** (health, live, ready, auth 401,
   protected surfaces 403, one VSR + one MOR, dashboard, risk-matrix, report generation).
5. **Confirm UAT-005 is resolved.**
6. **Record deployment timestamp and deployed commit hash.**
7. **Confirm the production environment matches the validated repository.**

**RC-6 (not started):** per phase governance, RC-6 begins only upon approval and completion of the
pending operator actions above.

---

## RC-5.5 Completion Report

**Date:** 2 August 2026
**Phase:** RC-5.5 — Live Deployment Validation & Production Candidate Verification
**Outcome:** **RC-5.5 FAILED – DEPLOYMENT VALIDATION FAILED**

### Deployment Status

Independent verification against the validated RC-5 candidate (02 Aug 2026):

- **Backend mismatch (Critical):** live build = committed HEAD `4e306ce` (pre-RC-1 hardening). Live
  OpenAPI shows admin POST `security: null` (candidate: `[{"HTTPBearer":[]}]`); legacy
  `/check-data`, `/migrate-seed-data`, `/auth/debug-verify` are live; no-token admin POST returns
  422 (body first — auth not enforced) instead of 403; `/seed-demo-data` and `/create-seed-users`
  are alive (not 404) and gated only by the hardcoded public `SETUP_SECRET`.
- **Frontend mismatch (Critical):** `gap-analysis-ssp.web.app` returns "Site Not Found" (no Hosting
  release/channels for the site); `sms.`/`app.aviasafesystems.com` have no DNS; the backend CORS
  allow-list trusts exactly the unreachable `gap-analysis-ssp.web.app` origin.
- **Root cause:** the RC-1→RC-5 fixes are **uncommitted** in the repository; a deploy built from
  committed history reproduces the vulnerable pre-RC-1 build. The validated candidate was never
  committed, so the deployment could not produce it.

### Smoke Test Results

API surfaces respond (health/live/ready 200; invalid-token 401; protected surfaces 403), but:
admin API → 422 no-auth (FAIL); destructive endpoints alive (FAIL); all frontend pages unreachable
(Firebase Hosting offline). Full matrix in `LIVE_DEPLOYMENT_VALIDATION_REPORT.md` §4.

### Environment Validation

Security headers present; auth verify/register present; Firestore connected; **admin
authorization NOT enforced**; **legacy debug/destructive endpoints present**; **frontend Hosting not
serving**; no automated backups (unchanged).

### Security Validation

RC-1 fixes are **NOT active** in production: no legacy admin endpoints (FAIL — present), no
setup-secret bypass (FAIL — public hardcoded key is the only gate), correct authorization (FAIL),
destructive endpoints disabled (FAIL — alive).

### Remaining Risks

Critical: R-1 live un-hardened backend; R-2 frontend offline; R-3 deployed build ≠ validated
candidate. High: no Firestore backups/PITR. Others unchanged (TD-12, self-registration, `/docs`).

### Recommendation

**RC-5.5 FAILED – DEPLOYMENT VALIDATION FAILED.** Corrective actions required before re-validation:
(1) commit the RC-1→RC-5 working-tree changes; (2) re-deploy the backend from the committed
candidate; (3) redeploy the frontend to Firebase Hosting; (4) re-run the validation checklist
(admin `security: HTTPBearer`, legacy paths 404, no-token admin 403, destructive endpoints 404,
frontend 200) and confirm UAT-005 CLOSED. RC-6 must not begin.

**RC-6 (not started):** per phase governance, RC-6 begins only upon approval and completion of the
corrective actions above.

---

## RR-1 Release Recovery Report

**Date:** 2 August 2026
**Phase:** RR-1 — Repository & Deployment Recovery
**Status:** **READY FOR REPOSITORY COMMIT**

### Trigger

RC-5.5 failed as a **release management failure**: the validated RC-1…RC-5 changes existed only in
the working tree and were never committed, so deployed history reproduced the pre-RC-1 build.

### Repository Recovery

- HEAD `4e306ce` is the pre-RC-1 baseline; branch `main`; remote
  `origin/DHFactors/aviasafe-unified-platform`; no tags; nothing staged.
- Working tree verified as the **complete validated candidate**: 46 tracked changes (45 modified +
  `README-sms.md` deleted) + 20 new files = 66 files, all enumerated in `RELEASE_RECOVERY_REPORT.md` §3.
- Completeness checks passed: working tree contains the RC-1 hardening the live build lacks
  (env-only `SETUP_SECRET` + `compare_digest`, `get_admin_user` on admin routes, destructive
  endpoints 404, legacy `/check-data` `/migrate-seed-data` `/auth/debug-verify` removed). No `.env`
  tracked; no hardcoded keys; `.env.example` is placeholder-only and safe to commit.

### Release Inventory

Full per-phase inventory (RC-1 security, RC-2 functional, RC-3 docs, RC-4 UAT evidence, RC-5
operational docs, RC-5.5/RR-1 evidence) is in `RELEASE_RECOVERY_REPORT.md` §3. **No validated work
exists only as uncommitted modifications outside this inventory.**

### Commit Recommendation

**Single atomic release commit** (recommended; stated explicitly): phase boundaries cannot be
reconstructed from the uncommitted tree, and atomicity guarantees the deployed artifact matches
the tested candidate. Message and rationale in `RELEASE_RECOVERY_REPORT.md` §4. Commit + push to
`origin/main` are **deferred pending approval** (not executed in RR-1).

### Release Tag Recommendation

**`v1.0.0-rc5`** (annotated) on the release commit; future RC-6 → `v1.0.0-rc6`.

### Deployment Checklist

Step-by-step runbook in `RELEASE_RECOVERY_REPORT.md` §6: preconditions (commit+tag), backend
Render deploy from the tag, env/secrets (`FIREBASE_PRIVATE_KEY`, `SETUP_SECRET`,
`DISABLE_DESTRUCTIVE_ENDPOINTS=True`, provision/seed passwords), frontend Firebase Hosting deploy,
immediate post-deploy checks, and rollback procedure.

### Verification Checklist

Post-deploy checklist in `RELEASE_RECOVERY_REPORT.md` §7: backend version, frontend 200,
no-token admin 403 (not 422), legacy/destructive endpoints 404, `security: HTTPBearer`, smoke,
security headers, tenant isolation, admin endpoint dual-factor, and UAT-005 closure criteria.

### Remaining Risks

R-1 commit/tag not executed or wrong commit; R-2 `FIREBASE_PRIVATE_KEY` escaping; R-3 CORS origin
mismatch; R-4 reused public `SETUP_SECRET`; R-5 UAT-005 closed without verification; R-6 backups;
R-7 `/docs` exposure. Full table in `RELEASE_RECOVERY_REPORT.md` §8.

### Recommendation

Approve the single release commit + `v1.0.0-rc5` tag; commit and push; execute §6 deployment and
§7 verification; re-run RC-5.5 validation against the deployed tag; close UAT-005; then RC-6.

**Phase declaration: READY FOR REPOSITORY COMMIT** — awaiting approval. No commit, deploy, RC-5.5,
or RC-6 activity performed.


