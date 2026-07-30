# PROJECT_STATUS.md

**Project:** AviaSAFE SMS Platform
**Status:** Production-Ready (Release Candidate)
**Version:** Release Candidate 1.0
**Last Updated:** 30 July 2026

---

## 1. Repository State

| Item | Status |
|------|--------|
| **Branch** | `main` (single branch, tracking `origin/main`) |
| **HEAD commit** | `70a96b6` — *chore: demote diagnostic logs from info to debug in repository and dashboard service* |
| **Working tree** | 2 modified files, 1 untracked file |
| **Tags** | None |
| **Stale/debug endpoints** | `/check-data`, `/fix-timestamps`, `/migrate-seed-data`, `/create-seed-users` — debug/admin endpoints for seed data migration; safe behind `setup_key` guard |

### Unstaged Changes
| File | Change |
|------|--------|
| `.firebase/hosting.cHVibGlj.cache` | Hosting deployment cache updated (hash for `js/firebase.js` refreshed) |
| `.gitignore` | Added `recaptch.txt` / `*recaptch*` patterns to prevent secret key leaks |
| `public/js/firebase.js` | reCAPTCHA key replaced with live key; App Check uses `ReCaptchaV3Provider` |
| `PROJECT_STATUS.md` | This file — comprehensive status update |
| `public/docs/tenant-guide/` (new) | Docs-as-code directory structure (manifest, templates, overview) |
| `tests/e2e/` (new) | E2E test scripts relocated from project root |
| `tests/README.md` (new) | Test directory documentation |
| `scripts/firebase/` (new) | Firebase admin scripts relocated from project root |
| `scripts/seed/` (new) | Seed data scripts relocated from project root |
| `test_super.py` (deleted) | Removed — duplicate of `e2e_diag.py` |

### Recent Commits (3 most recent)

| Commit | Date | Description |
|--------|------|-------------|
| `70a96b6` | 30 Jul 08:46 | Demoted diagnostic `logger.info` → `logger.debug` in repository.py and dashboard_service.py |
| `c1fa7f6` | 30 Jul 08:35 | Normalized `tenant_id` underscores→hyphens in auth middleware; added Firestore diagnostics (raw doc counts, field inspection); added date-filter fallback when date filter returns 0 results but raw docs exist |
| `c8c252a` | 30 Jul 07:08 | Added App Check bypass guards: `?appcheck=false` URL param, localhost detection, placeholder key validation |

---

## 2. Database Setup (Firestore)

### Project
- **Firebase Project ID:** `gap-analysis-ssp`
- **Firestore Location:** `nam5` (US multi-region)
- **Alias:** `smssurvey` (in `.firebaserc`)

### Collections & Data Model
All tenant data is isolated under `/tenants/{tenant_id}/`:

| Subcollection | Purpose | Access Level |
|---|---|---|
| `metadata/{doc}` | Tenant configuration, survey settings | SUPER_ADMIN write; tenant+Caan read |
| `responses/{id}` | Survey responses (930 seeded) | Public create; immutable; tenant+Caan read |
| `reports/{id}` | VSR reports (620 seeded) | Public create; tenant+Caan read; update allowed |
| `mor/{id}` | MOR reports (245 seeded) | Auth create; tenant+Caan read; update allowed |
| `hazards/{id}` | Safety hazards (auto-created from reports) | Auth create; full CRUD by tenant |
| `can_cap/{id}` | Corrective Action Notices/Plans | Auth create; full CRUD by tenant |
| `verification/{doc}` | Hazard verifications & closures | Auth create; full CRUD by tenant |
| `flight_diversions/{doc}` | Flight diversion records | Auth create; full CRUD by tenant |

Root-level collections:
| Collection | Purpose |
|---|---|
| `analytics/{doc}` | Aggregate analytics (CAAN_SMD and SUPER_ADMIN only) |
| `public_responses/{doc}` | Public survey responses |
| `users/{uid}` | User profiles |

### Security Rules (`firestore/firestore.rules`)
- **Roles enforced:** `SUPER_ADMIN` (full), `CAAN_SMD` (cross-tenant read), `AIRLINE_ADMIN` (tenant-scoped), `USER` (basic authenticated)
- **Immutable audit trail:** Responses/reports cannot be deleted
- **Public submission:** VSR reports and survey responses allow unauthenticated creation (anonymous safety reporting)
- **CAAN Just Culture:** CAAN has cross-tenant read access but no write/delete; dashboard is anonymized
- **Tenant isolation:** `isOwnTenant()` validates `tenant_id` matches the request auth token claim

### Composite Indexes (`firestore.indexes.json`)
6 indexes deployed:
- `responses` → `submittedAt` DESC
- `reports` → `submittedAt` DESC
- `reports` → `reportType` ASC, `submittedAt` DESC
- `reports` → `status` ASC, `submittedAt` DESC
- `classifications` → `occurrenceType` ASC, `createdAt` DESC
- `metrics` → `metricType` ASC, `updatedAt` DESC

**Note:** A secondary `backend/firestore.indexes.json` exists with `collection_group`-scoped indexes using snake_case field names — this is not deployed. The root-level file is authoritative.

### Seed Data
| Dataset | Count |
|---------|-------|
| Operators (airlines) | 6 active / 20 provisioned |
| Survey Responses | 930 |
| VSR Reports (voluntary) | 620 |
| MOR Reports (mandatory) | 245 |
| Firestore Documents (total) | ~1,808 |
| Auth Users (provisioned) | 21+ |

### Known Seed Data Issues
- **Tenant ID mismatch (resolved):** Seed data used underscore IDs (`buddha_air`); provisioned users used hyphens (`buddha-air`). Migration endpoint `/migrate-seed-data` and `/fix-tenant-ids` were deployed and run.
- **ISO string timestamps (resolved):** Old seed data stored dates as ISO strings instead of Firestore Timestamps. `/fix-timestamps` endpoint remediated this. Repository layer retains a **fallback** that retries queries without date filter when date-filtered queries return 0 results but raw docs exist.

---

## 3. App Check Configuration

### Frontend (`public/js/firebase.js:166`)

```
RECAPTCHA_SITE_KEY = '6LeCcWwtAAAAAFK2Y3hwxjO3pHGX6xaFxFIzF6Jv'  (live key)
```

### Initialization
```js
firebase.appCheck().activate(
    new firebase.appCheck.ReCaptchaV3Provider(RECAPTCHA_SITE_KEY),
    true  // token auto-refresh enabled
);
```

### Bypass Conditions
App Check is skipped when any of the following are true:
1. URL contains `?appcheck=false` query parameter
2. Hostname is `localhost` or `127.0.0.1` (local development)
3. `RECAPTCHA_SITE_KEY.length < 20` (invalid/placeholder key)

### Backend App Check
The **backend** does not enforce App Check tokens. Firebase Admin SDK bypasses App Check by design (service account credentials are used instead). App Check is enforced client-side only.

### Status
- **Client:** ✅ Active — reCAPTCHA v3 with live site key, auto-refresh on
- **Backend:** ✅ Bypassed by design (Admin SDK uses service account)
- **Secret key:** Stored in untracked `recaptch.txt` file — not in version control

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Firebase Hosting)                                │
│  public/ — 29 HTML pages, 15 core JS modules               │
│    ┌─────────────────────────────────────────────────┐      │
│    │  firebase.js → App Check → Auth → API Client    │      │
│    └─────────────────────────────────────────────────┘      │
│  src/ — Astro marketing pages (index + layout)              │
└──────────┬──────────────────────────────────────────────────┘
           │ HTTPS (JWT Bearer Token)
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI — Render / Cloud Run)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Auth     │  │ Routes   │  │ Services │  │ Models   │   │
│  │ Middleware│→ │ (9 mods) │→ │(12 mods) │→ │ (11 mods)│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Firebase Admin SDK → Firestore (gap-analysis-ssp) │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Gemini 2.5 Pro AI → risk assessment & taxonomy   │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns
- **Multi-tenant:** Data fully isolated by `tenant_id` in Firestore path
- **Role-based access:** 4 roles (USER, AIRLINE_ADMIN, CAAN_SMD, SUPER_ADMIN)
- **Dual API prefix:** `/api/v1/...` (primary) and `/api/...` (legacy, hidden from OpenAPI)
- **Repository pattern:** In-memory LRU cache (60s TTL) for dashboard queries
- **AI integration:** Async Gemini analysis on report submission; ICAO risk assessment (severity × probability)
- **Rate limiting:** Redis-backed (Upstash) with 5 limit types; in-memory fallback per IP (60 req/min)

---

## 5. Backend Service Status

### API Routes (143 total)
| Router | Prefix | Endpoints |
|--------|--------|-----------|
| Auth | `/api/v1/auth` | 4 (verify, debug-verify, register, refresh) |
| Reports | `/api/v1/reports` | 6 (create VSR, create MOR, list, get, risk-assessment, auto-hazard) |
| Dashboard | `/api/v1/dashboard` | 13 (airline × 6, CAAN × 5, admin × 3) |
| Admin | `/api/v1/admin` | 7 (risk-matrix CRUD, setup-claims, seed data, provisioning, migration) |
| Hazards | `/api/v1/hazards` | 7 (CRUD, stats, status, assign) |
| CAN/CAP | `/api/v1/cans` | 11 (CAN CRUD, CAP submit/list/review) |
| Verification | `/api/v1/verification` | 7 (verification CRUD, closure, reopen) |
| Reporting | `/api/v1/reporting` | 8 (quarterly/annual generation, list, get, PDF export) |
| Flight Diversions | `/api/v1/flight-diversions` | 8 (CRUD, stats, hazard linking) |
| Metrics | `/metrics` | 1 (Prometheus-style) |
| Health | `/health`, `/live`, `/ready`, `/` | 4 |

### Services (12 modules)
| Service | Purpose |
|---------|---------|
| `Repository` | Firestore query builder, pagination (cursor-based), caching |
| `MetricsService` | KPI/trend/risk-distribution calculations |
| `DashboardService` | Role-aware orchestration for all dashboard endpoints |
| `ReportService` | VSR/MOR CRUD with auto-AI analysis trigger |
| `HazardService` | Hazard register CRUD, status workflow |
| `CanCapService` | Corrective Action Notice/Plan lifecycle |
| `VerificationService` | Hazard verification, closure, reopening |
| `FlightDiversionService` | Diversion CRUD + hazard linking |
| `ReportGenerator` | Quarterly/annual safety report generation (PDF) |
| `Gemini` | AI analysis via Google Gemini 2.5 Pro |
| `RiskMatrix` | ICAO 5×5 severity×probability → risk index |
| `PDFGenerator` | ReportLab-based PDF export with placeholder fallback |

### Authentication & Authorization
- **Token verification:** Firebase Admin SDK `verify_id_token()` with RS256
- **Role resolution:** Custom claims from token → fallback to Firestore tenant lookup if claims not yet propagated
- **Tenant normalization:** Underscores → hyphens in `tenant_id` (handles provisioned vs seed data mismatch)
- **Role guards:** 6 dependency guard functions (tenant_user, caan_user, admin_user, safety_manager, responsible_manager, accountable_executive)

### Middleware Stack (order of execution)
1. `SecurityHeadersMiddleware` — HSTS, nosniff, DENY framing, XSS protection, referrer policy, permissions policy
2. `RateLimitMiddleware` — 60 req/min per IP (in-memory); Redis-backed per-tenant limits on auth/report endpoints
3. `RequestLoggingMiddleware` — Request UUID, method/path/status/duration/user logging

---

## 6. Frontend Service Status

### Pages (29 HTML files)
| Section | Pages | Status |
|---------|-------|--------|
| **Core** | Landing, Login, Safety Dashboard, CAAN Dashboard | ✅ |
| **Survey** | Survey app (bilingual EN/NP), Survey Period Admin Dashboard | ✅ |
| **VSR/MOR** | VSR submission, MOR submission, Report detail, Report list | ✅ |
| **Hazards** | Hazard register, Create, Detail, Verify, Approve closure | ✅ |
| **CAN/CAP** | CAN list, Detail, CAP submit, CAP review | ✅ |
| **Flight Diversions** | List, Detail, Create | ✅ |
| **Reporting** | Report generation, Quarterly/Annual list & PDF export | ✅ |
| **Admin** | Tenant & user management, system stats | ✅ |
| **Portal** | Tenant portal, Portal dashboards, Portal survey | ✅ |

### JavaScript Modules (15 core)
| Module | Purpose |
|--------|---------|
| `firebase.js` | Firebase init, App Check, auth helpers (`getCurrentUser`, `waitForFirebase`) |
| `api/client.js` | `ApiClient` singleton — auto-auth token injection, 401 redirect |
| `api/dashboard.js` | Dashboard API calls |
| `dashboard.js` | Survey dashboard rendering |
| `dashboard-utils.js` | Chart/table helpers |
| `vsr.js` | VSR form submission & validation |
| `mor.js` | MOR form submission & validation |
| `reports.js` | Report listing |
| `report.js` | Report detail view |
| `hazards.js` | Hazard CRUD |
| `verification.js` | Verification/closure workflow |
| `can_cap.js` | CAN/CAP lifecycle |
| `flight_diversions.js` | Diversion CRUD |
| `tenant.js` | Tenant-specific logic |

### Firebase Hosting Config
- **Static assets:** 7-day cache (images), 1-day cache (JS/CSS), both `immutable`
- **SPA rewrite:** All routes → `/index.html`
- **Security headers:** X-Content-Type-Options (nosniff), X-Frame-Options (DENY), X-XSS-Protection (1; mode=block), Referrer-Policy (strict-origin-when-cross-origin)
- **CDN-first loading:** Firebase SDK loaded via static `<script>` tags in HTML (race condition eliminated)

---

## 7. Recent Backend/Frontend Changes

### Backend Changes (last 3 commits)

**Repository Layer** (`backend/app/services/repository.py`):
- Demoted verbose field-level diagnostic logging from `info` → `debug`
- Added raw doc count logging before filtered queries for debugging zero-result scenarios
- Added date-filter fallback: when date-filtered query returns 0 results but raw docs exist, retries without date filter (handles ISO-string timestamps in old seed data)
- Changed `Query.DESCENDING`/`Query.ASCENDING` import to use `google.cloud.firestore.Query` (avoid deprecation)

**Dashboard Service** (`backend/app/services/dashboard_service.py`):
- Demoted `logger.info` → `logger.debug` in `_base_filter()`
- Added request/response logging in `get_dashboard_overview` route

**Auth Middleware** (`backend/app/middleware/auth.py`):
- Added `tenant_id` normalization: underscores → hyphens in token claims
- Added info log of final authenticated user

### Frontend Changes (unstaged)
**App Check** (`public/js/firebase.js`):
- **reCAPTCHA key:** Replaced placeholder `'6LcAAAAA'` with live key `'6LeCcWwtAAAAAFK2Y3hwxjO3pHGX6xaFxFIzF6Jv'`
- **Provider pattern:** Changed `firebase.appCheck().activate(key, true)` → `firebase.appCheck().activate(new firebase.appCheck.ReCaptchaV3Provider(key), true)` (uses modular SDK provider pattern)
- **Validation:** Removed stale placeholder literal check; now validates by length only (`RECAPTCHA_SITE_KEY.length < 20`)
- Changes are **unstaged** — ready for commit

### Infrastructure Changes
- No deployment configuration changes
- Hosting cache (`hosting.cHVibGlj.cache`) auto-updated on last deploy

---

## 8. Testing Status

### Unit/Integration Tests (`backend/tests/`)
| Test Suite | Tests | Status |
|-----------|-------|--------|
| `test_health.py` | 3 | ✅ All pass — health, live, root endpoints |
| `test_metrics_service.py` | 7 | ✅ All pass — KPI calculations, risk distribution, trends, AI/organizational KPIs |
| `test_risk_assessment_lifecycle.py` | 4 (scenarios) | ✅ All pass — submission auto-calculation, AI suggestions, Safety Manager override, RBAC enforcement (600 lines, full Firestore mock stack) |

### End-to-End Tests (`tests/e2e/`)
| Script | Purpose | Status |
|--------|---------|--------|
| `e2e_test.py` | 10-scenario comprehensive E2E (VSR, MOR, hazards, CAN/CAP, verification, reporting, diversions, dashboards, RBAC) | ✅ |
| `e2e_test2.py` | Round 2 — simplified assertions, alternate-path resilience probing | ✅ |
| `e2e_auth.py` | Token acquisition & endpoint smoke test | ✅ |
| `e2e_diag.py` | Token decoding & endpoint accessibility diagnostics | ✅ |
| `e2e_route_check.py` | OpenAPI spec route inspection | ✅ |
| `e2e_setup_claims.py` | One-shot claims setup via `/api/v1/admin/setup-claims` | ✅ |
| `test_dash.py` | Quick dashboard test with Buddha Air tenant | ✅ |
| `e2e_tokens.json` | Token cache (generated by `e2e_auth.py`) | — |

### Scripts (`scripts/`)
| Directory | Scripts | Purpose |
|-----------|---------|---------|
| `firebase/` | `delete-users.js`, `set-claims.js`, `verify-claims.js` | Firebase Admin SDK user management |
| `seed/` | `run_seed.py`, `check_seed.py` | Seed data utilities |

### E2E Test Credentials
| User | Email | Role | Tenant | Password |
|------|-------|------|--------|----------|
| Admin | `admin@aviasafesystems.com` | SUPER_ADMIN | — | Admin123! |
| Sal | `sal@aviasafesystems.com` | AIRLINE_ADMIN | sita-air | Sal123! |
| Salsafety | `salsafety@aviasafesystems.com` | AIRLINE_ADMIN | sita-air | Safety123! |
| SMD | `smd@caanepal.gov.np` | CAAN_SMD | — | Smd123! |

---

## 9. Infrastructure & Deployment

### Current Deployment (Prototype)
| Component | Provider | URL |
|-----------|----------|-----|
| **Frontend** | Firebase Hosting (Spark) | `https://gap-analysis-ssp.web.app` |
| **Backend** | Render (Free) | `https://aviasafe-unified-platform.onrender.com` |
| **Database** | Firestore (nam5) | — |
| **Auth** | Firebase Authentication | — |
| **AI** | Google Gemini 2.5 Pro | — |
| **Rate Limiting** | Upstash Redis | — |

### Target Deployment (Commercial)
| Component | Provider |
|-----------|----------|
| **Frontend** | Firebase Hosting (Blaze) |
| **Backend** | Google Cloud Run (512MB, 1CPU, 1-10 instances) |
| **Domain** | `sms.aviasafesystems.com` |

### Containerization
- **Dockerfile:** Python 3.11-slim, pip install from requirements.txt, uvicorn on port 8000
- **docker-compose.yml:** Single `api` service, health checks via `/live`, 512MB memory limit
- **cloudrun.yaml:** Knative Service config with health probes at `/live` and `/ready`
- **render.yaml:** Render Blueprint Docker deployment with env vars

### Key Environment Variables (backend)
| Variable | Source | Purpose |
|----------|--------|---------|
| `FIREBASE_PROJECT_ID` | `.env` / Render secrets | Firebase Admin SDK |
| `FIREBASE_PRIVATE_KEY` | `.env` / Render secrets | Service account private key |
| `FIREBASE_CLIENT_EMAIL` | `.env` / Render secrets | Service account email |
| `GEMINI_API_KEY` | `.env` / Render secrets | Google Gemini AI |
| `REDIS_URL` | `.env` | Upstash Redis for rate limiting |
| `ALLOWED_ORIGINS` | `.env` / Render | CORS origins (Firebase, localhost) |
| `REDIS_ENABLED` | `.env` | Toggle Redis rate limiting |

---

## 10. Known Issues & Risks

| Issue | Severity | Status |
|-------|----------|--------|
| Debug endpoints (`/check-data`, `/fix-timestamps`, etc.) exposed on production API | **MEDIUM** | Behind `setup_key` guard — acceptable for now |
| Claims propagation delay — token may lack custom claims immediately after set | **LOW** | Handled via tenant email lookup fallback in auth middleware |
| Date-filter fallback in repository may return stale data if ISO strings exist | **LOW** | Seed data migration to Timestamps complete; fallback is a safety net |
| No Cloud Functions deployed (`functions/` is empty) | **LOW** | Not yet required — all logic lives in backend API |

## 11. Documentation-as-Code Setup

A tenant onboarding documentation framework has been established under `public/docs/tenant-guide/`:

| Artifact | Path | Purpose |
|----------|------|---------|
| **Manifest** | `public/docs/tenant-guide/manifest.json` | Maps steps 01–03 with IDs, titles, descriptions, and file references |
| **Template** | `public/docs/tenant-guide/templates/STEP_DOCUMENTATION_TEMPLATE.md` | Standard multi-layer format: Overview, Step-by-Step UI Guide with input matrix, Edge Cases, QA Checklist |
| **Step 01** | `public/docs/tenant-guide/01-getting-started/1.0-overview.md` | First live doc — login, platform orientation, role-based dashboard walkthrough |

The template enforces a consistent structure across all future steps:
1. **Overview** — purpose, business context, expected outcome
2. **Step-by-Step UI Guide** — navigation, input matrix (field/type/required/constraints/notes), execution, success confirmation
3. **Edge Cases** — scenarios, common errors with cause and resolution
4. **QA Checklist** — verification points for testing each step

### Planned Steps (manifest)
| Step | ID | Title |
|------|----|-------|
| 01 | `01-getting-started` | Getting Started |
| 02 | `02-account-setup` | Account & Profile Setup |
| 03 | `03-safety-reporting` | Safety Reporting (VSR / MOR) |

## 12. Immediate Next Steps

| Priority | Task |
|----------|------|
| **P1** | **UAT** — User Acceptance Testing with seed data validation |
| **P2** | **Expand docs** — Create steps 02 (Account Setup) and 03 (Safety Reporting) |
| **P3** | **Airline Pilot** — Onboard first airline tenant |
| **P4** | **CAAN Pilot** — Onboard CAAN SSP regulatory oversight |
| **P5** | **Production Go-Live** — Migrate from Render free tier to Cloud Run |
| **P6** | **Survey Visualization** — Survey results dashboard on airline dashboard |

### Completed (Commit 2 — Repository Reorganisation)
- Root-level E2E scripts moved to `tests/e2e/` (7 files + 1 deleted duplicate)
- Firebase admin scripts moved to `scripts/firebase/` (3 files)
- Seed data scripts moved to `scripts/seed/` (2 files)
- `tests/README.md` created documenting directory structure and run instructions
- All moves use `git mv` to preserve history

---

## 13. Configuration Summary

```
Firebase Project:     gap-analysis-ssp (alias: smssurvey)
Frontend Domain:      gap-analysis-ssp.web.app
Backend API:          aviasafe-unified-platform.onrender.com
Firestore Location:   nam5 (US multi-region)
Firebase SDK:         v9.22.0 (compat)
Astro:                Static (marketing pages)
Tailwind:             3.x (Astro pages only)
FastAPI:              0.109.0
Python:               3.11-slim (Docker)
Gemini Model:         gemini-2.0-pro-exp-02-05
Rate Limiting:        Upstash Redis + in-memory fallback
Auth:                 Firebase Authentication (JWT Bearer tokens)
Roles:                USER, AIRLINE_ADMIN, CAAN_SMD, SUPER_ADMIN
reCAPTCHA v3 Key:     6LeCcWwtAAAAAFK2Y3hwxjO3pHGX6xaFxFIzF6Jv (live)
App Check:            Active (client-side), auto-refresh enabled
```
