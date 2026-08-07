# API Reference

AviaSAFE backend API. Base URL (live): `https://aviasafe-unified-platform.onrender.com`

- Interactive docs: `{base}/docs` (Swagger UI)
- ReDoc: `{base}/redoc`
- OpenAPI JSON: `{base}/openapi.json`
- Health: `{base}/health`, `/live`, `/ready`, `/metrics`

## 1. Authentication

All business endpoints require a Firebase ID token:

```
Authorization: Bearer <FIREBASE_ID_TOKEN>
```

- The client obtains the token via Firebase Auth (email/password) using `public/js/firebase.js`.
- The backend verifies with the Firebase Admin SDK (RS256).
- Role/tenant resolution: custom claims (primary); email→tenant fallback when claims have not
  propagated.
- On `401` the client redirects to login. `403` means authenticated but not authorized for the
  action.
- Admin provisioning endpoints additionally require `X-Setup-Key: <SETUP_SECRET>` (503 when unset).

### Roles

| Role | Access |
|---|---|
| `SUPER_ADMIN` | Everything, cross-tenant, admin endpoints |
| `CAAN_SMD` | Cross-tenant read + risk-assessment confirm |
| `AIRLINE_ADMIN` | Own tenant full access, risk-matrix config, confirm assessments |
| `USER` | Own tenant submit/read |

## 2. Conventions

- Canonical prefix: **`/api/v1`**. Legacy aliases (`/api/...`) exist for backward compatibility and
  are hidden from OpenAPI.
- Response envelope: JSON objects/arrays directly; errors use FastAPI/HTTPException shape
  (`detail`).
- Pagination on list endpoints returns `{data: [...], page, page_size, total, has_more}` style
  (cursor/page per repository).

## 3. Endpoint Inventory (verified against the running app, RC-3)

> Inventory below lists the canonical `/api/v1` paths. 73 business endpoints + system endpoints.
> Every `/api/v1` path also has a legacy `/api` twin.

### 3.1 Auth — `/api/v1/auth`

| Method | Path | Description |
|---|---|---|
| POST | `/register` | Register a user (role default `AIRLINE_ADMIN`) |
| POST | `/verify` | Verify an ID token |
| POST | `/refresh` | Refresh token exchange |

### 3.2 Admin — `/api/v1/admin` (SUPER_ADMIN; `*` = requires `SETUP_SECRET`)

| Method | Path | Description |
|---|---|---|
| POST | `/setup-claims` | Resolve/create role & tenant claims |
| POST | `/provision-airlines` * | Provision tenants + admins + CAAN accounts |
| POST | `/fix-tenant-ids` | Reconcile `_`/`-` tenant id drift |
| GET | `/risk-matrix` | Read default risk matrix |
| PUT | `/risk-matrix` * | Update default risk matrix |
| POST | `/seed-demo-data` * | Destructive re-seed (404 when disabled) |
| POST | `/create-seed-users` * | Recreate seed users (404 when disabled) |

### 3.3 Reports — `/api/v1/reports`

| Method | Path | Description |
|---|---|---|
| POST | `/` | Create report (VSR or MOR) — triggers background AI analysis |
| GET | `/` | List reports (tenant-scoped) |
| POST | `/vsr` | Create VSR specifically |
| POST | `/mor` | Create MOR specifically |
| GET | `/{report_id}` | Get report detail |
| PUT | `/{report_id}/risk-assessment` | Confirm risk assessment (Safety Manager / CAAN_SMD) |

Report types: `vsr` (Voluntary Safety Reporting), `mor` (Mandatory Occurrence Reporting). Risk
fields: `severity_level`, `probability_level`, `risk_index`, `risk_level`, `risk_assessment`
(official), `ai_suggested_assessment` (AI suggestion — never authoritative). Legacy fields
(`risk_score`, `severity`, `likelihood`, `consequence`) retained for compatibility.

### 3.4 Hazards — `/api/v1/hazards`

| Method | Path | Description |
|---|---|---|
| POST | `/` | Create hazard (also auto-created from reports) |
| GET | `/` | List hazards |
| GET | `/stats` | Hazard statistics |
| GET | `/{hazard_id}` | Get hazard |
| PUT | `/{hazard_id}` | Update hazard |
| PATCH | `/{hazard_id}/assign` | Assign responsible manager |
| PATCH | `/{hazard_id}/status` | Change status |

### 3.5 CAN/CAP — `/api/v1/cans`

| Method | Path | Description |
|---|---|---|
| POST | `/` | Create CAN |
| GET | `/` | List CANs |
| GET | `/stats` | CAN/CAP statistics |
| GET | `/caps/{cap_id}` | Get CAP |
| PATCH | `/caps/{cap_id}` | Update CAP |
| PATCH | `/caps/{cap_id}/review` | Review CAP |
| PATCH | `/caps/{cap_id}/status` | CAP status transition |
| GET | `/{can_id}` | Get CAN |
| DELETE | `/{can_id}` | Delete CAN |
| POST | `/{can_id}/caps` | Create CAP under a CAN |
| GET | `/{can_id}/caps` | List CAPs of a CAN |
| PATCH | `/{can_id}/status` | CAN status transition |

### 3.6 Verification — `/api/v1/verification`

| Method | Path | Description |
|---|---|---|
| POST | `/hazards/{hazard_id}/closure` | Request/record hazard closure |
| GET | `/hazards/{hazard_id}/closure` | Get closure record |
| PATCH | `/hazards/{hazard_id}/reopen` | Reopen a closed hazard |
| POST | `/hazards/{hazard_id}/verifications` | Create verification |
| GET | `/hazards/{hazard_id}/verifications` | List verifications |
| GET | `/verifications/stats` | Verification statistics |
| GET | `/verifications/{verification_id}` | Get verification |

### 3.7 Flight Diversions — `/api/v1/flight-diversions`

| Method | Path | Description |
|---|---|---|
| POST | `/` | Create diversion |
| GET | `/` | List diversions |
| GET | `/stats` | Diversion statistics |
| GET | `/{diversion_id}` | Get diversion |
| PATCH | `/{diversion_id}` | Update diversion |
| DELETE | `/{diversion_id}` | Delete diversion |
| POST | `/{diversion_id}/link-hazard` | Link a hazard |
| DELETE | `/{diversion_id}/link-hazard` | Unlink a hazard |

### 3.8 Reporting — `/api/v1/reporting`

| Method | Path | Description |
|---|---|---|
| POST | `/annual` | Generate annual report |
| GET | `/annual` | List annual reports |
| GET | `/annual/{report_id}` | Get annual report |
| GET | `/annual/{report_id}/export` | Export PDF |
| POST | `/quarterly` | Generate quarterly report |
| GET | `/quarterly` | List quarterly reports |
| GET | `/quarterly/{report_id}` | Get quarterly report |
| GET | `/quarterly/{report_id}/export` | Export PDF |

### 3.9 Dashboard — `/api/v1/dashboard`

| Method | Path | Description |
|---|---|---|
| GET | `/overview` | Overview KPIs (tenant / CAAN) |
| GET | `/recent` | Recent reports |
| GET | `/actions` | Pending actions |
| GET | `/risk` | Risk distribution |
| GET | `/trends` | Trends (default 180 days) |
| GET | `/hazards` | Hazard metrics |
| GET | `/caan/overview` | CAAN overview |
| GET | `/caan/benchmark` | Cross-tenant benchmark |
| GET | `/caan/risk` | CAAN risk view |
| GET | `/caan/hazards` | CAAN hazard view |
| GET | `/caan/trends` | CAAN trends |
| GET | `/admin/system` | System status (SUPER_ADMIN) |
| GET | `/admin/tenants` | Tenant list (SUPER_ADMIN) |
| GET | `/admin/usage` | Usage analytics (SUPER_ADMIN) |

### 3.10 Surveys — `/api/v1/surveys`

Survey submission is **anonymous by default**: a Bearer token is optional. Public survey pages
submit without login; an authenticated user with a tenant may only submit to their own tenant
(cross-tenant roles may submit anywhere). Each response is validated against the master
question contract, scored server-side into the four ICAO pillars (1-5), persisted to
`tenants/{id}/surveys` (scored — feeds the airline + CAAN SMS health dashboards) and
`tenants/{id}/responses` (raw), and audited with `SURVEY_SUBMITTED`.

| Method | Path | Description |
|---|---|---|
| POST | `/` | Submit an ICAO-aligned survey response (validates + scores + persists) |

Request body:

```json
{
  "tenantId": "tara-air",
  "respondentId": "optional-employee@taraair.com",
  "answers": {
    "q1_aware": true,
    "q2": 4,
    "...": 1,
    "q23_peer": 5,
    "q24_comments": "Optional free text"
  },
  "department": "Flight Operations",
  "employee_category": "Pilot",
  "years_experience": "5-10",
  "language": "en"
}
```

Rules:
- All **23 scored questions** must be present (`q1_aware` binary → `true`/`false` or `1`/`5`;
  likert `q2`…`q23_peer` → `1-5`). `q24_comments` is optional free text.
- Pillar grouping: `safety_policy` = q1–q5, `safety_risk_management` = q6–q13,
  `safety_assurance` = q14–q16 + q19–q20, `safety_promotion` = q17–q18 + q21–q23.
- Responses: `201` with `{id, tenant_id, overall_sms_health, overall_score_pct, pillar_scores}`.
- Rate limited to **`SURVEY_RATE_LIMIT` submissions per tenant per day** (default 5, env-configurable;
  overridable per tenant via `tenants/{id}/config.survey_rate_limit`). Counter key: `rl:survey:{tenantId}:{date}`.

### 3.11 Tenants — `/api/v1/tenants`

Per-tenant configuration endpoints. Phase 1 ships the survey rate-limit control; Phase 3 extends
the same PUT contract with survey instructions and adds an auth-optional GET.

| Method | Path | Description |
|---|---|---|
| GET | `/{tenantId}/config` | Read tenant config (auth **optional**; public survey page) |
| GET | `/{tenantId}/users` | List authorized users (AIRLINE_ADMIN of that tenant or SUPER_ADMIN) |
| PUT | `/{tenantId}/config` | Update tenant config (AIRLINE_ADMIN of that tenant only) |

`GET /{tenantId}/config` returns the stored `config` map (missing fields omitted):

```json
{
  "status": "success",
  "timestamp": "...",
  "data": {
    "tenant_id": "tara-air",
    "config": {
      "survey_rate_limit": 25,
      "survey_instructions": "Please answer all questions honestly."
    }
  }
}
```

- Authentication is **optional**: the public survey page fetches `survey_instructions` without a login.
  A supplied but invalid token is still rejected with `401`.
- `404` for unknown tenants; tenants without a `config` field return an empty `{}` map.

`GET /{tenantId}/users` returns the view-only authorized-users list for a tenant:

```json
{
  "status": "success",
  "timestamp": "...",
  "data": {
    "tenant_id": "tara-air",
    "users": [
      { "uid": "abc", "email": "officer@taraair.com", "role": "AIRLINE_ADMIN",
        "createdAt": "2026-08-06T10:00:00+00:00", "lastLogin": null }
    ]
  }
}
```

- Authorization: `AIRLINE_ADMIN` of the target tenant or `SUPER_ADMIN` (`403` otherwise).
- Data source: the Firestore `users` collection, mirrored from Firebase Auth (backfilled via
  `backend/scripts/backfill_users.py` and maintained on register / claims updates).

`PUT /{tenantId}/config` request body:

```json
{
  "survey_rate_limit": 25,
  "survey_instructions": "Please answer all questions honestly."
}
```

- `survey_rate_limit` must be one of **5, 10, 25, 50, 100**.
- `survey_instructions` is an optional string (Rich Text / Markdown) shown at the top of the survey.
- Authorization: `AIRLINE_ADMIN` of the target tenant only (`403` otherwise). `404` for unknown tenant.
- Persists under the tenant doc's `config` map, preserving other keys. A `null` `survey_instructions`
  leaves the existing value untouched; passing an empty string clears it.
- Audited with `TENANT_CONFIG_UPDATED`. Responses use the `{status, timestamp, data}` envelope.

### 3.12 System

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service banner/info |
| GET | `/health` | Health |
| GET | `/live` | Liveness probe |
| GET | `/ready` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs`, `/redoc`, `/openapi.json` | API docs |

## 4. Example: Submit a VSR

```bash
curl -X POST https://aviasafe-unified-platform.onrender.com/api/v1/reports/vsr \
  -H "Authorization: Bearer <ID_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "vsr",
    "title": "Turbulence near XYZ",
    "description": "Severe turbulence encounter...",
    "severity_level": 3,
    "probability_level": 2,
    "category": "Operational"
  }'
```

Response includes the computed `risk_index` (severity × probability), `risk_level`, and
`risk_assessment` placeholders that the Safety Manager confirms via
`PUT /api/v1/reports/{id}/risk-assessment`.

## 5. Error Handling

| Code | Meaning |
|---|---|
| 400 | Validation error (`detail` describes the field) |
| 401 | Missing/invalid ID token |
| 403 | Authenticated but not authorized (role / tenant) |
| 404 | Not found (or disabled destructive endpoint) |
| 429 | Rate limited |
| 500 | Server error — check `backend/logs/` |
| 503 | Missing required env config (e.g., `SETUP_SECRET` unset) |
