# ICAO SMS Risk Assessment — Design Specification v1

## 1. Firestore Schema

### Report Document (tenants/{t}/reports/{r}) — New Fields

```
# New — stored directly on report
severity_level:    int | None     # 1-5 (ICAO: 1=Negligible … 5=Catastrophic)
probability_level: int | None     # 1-5 (ICAO: 1=Extremely Improbable … 5=Frequent)
risk_index:        int | None     # 1-25 (severity_level × probability_level)
risk_level:        str | None     # "Low" | "Medium" | "High" | "Very High" | "Extreme"

# Official assessment (confirmed by Safety Manager)
risk_assessment: {
    severity:        int
    probability:     int
    risk_index:      int
    risk_level:      str
    assessed_by:     str           # Firebase uid
    assessed_at:     str           # ISO 8601
    notes:           str | None
} | None

# AI suggestion (never authoritative)
ai_suggested_assessment: {
    suggested_severity:    int
    suggested_probability: int
    suggested_risk_index:  int
    suggested_risk_level:  str
    confidence:            float     # 0.0–1.0
} | None

# Legacy — kept for backward compatibility
risk_score:  float | None    # 0.0–1.0 (computed from risk_index ÷ 25)
severity:    str | None      # "Low" | "Medium" | "High" | "Critical"
likelihood:  str | None      # free-text (already exists)
consequence: str | None      # free-text (already exists)
```

### Tenant Metadata (tenants/{t}/metadata/risk_matrix) — New Document

```
{
    version:        "1.0",
    severity_labels:  { "1": "Negligible", "2": "Minor", "3": "Major",
                        "4": "Hazardous", "5": "Catastrophic" },
    probability_labels: { "1": "Extremely Improbable", "2": "Improbable",
                          "3": "Remote", "4": "Occasional", "5": "Frequent" },
    thresholds: { low_max: 5, medium_max: 9, high_max: 15 },
    risk_level_labels: { "Low": "Low (Acceptable)",
                         "Medium": "Medium (Tolerable)",
                         "High": "High (Intolerable)",
                         "Very High": "Very High (Intolerable – Immediate Action)" },
    updated_by: str,
    updated_at: str
}
```

The 5×5 matrix is **computed** as `S × P` (not stored). Thresholds are configurable per tenant.

---

## 2. API Changes

### POST /api/v1/reports — Extended input
Accept optional `severity_level` and `probability_level`. If both supplied, compute `risk_index` and `risk_level` immediately. If absent, remain `null` until assessment is confirmed. `risk_assessment` is NOT set here — only `ai_suggested_assessment` may be populated by background AI.

### PUT /api/v1/reports/{id}/risk-assessment — New
- **Auth:** AIRLINE_ADMIN or above
- **Body:** `{ severity: int, probability: int, notes?: string }`
- Computes `risk_index = S × P`, derives `risk_level` from tenant thresholds
- Sets `risk_assessment.assessed_by` to current user uid, `assessed_at` to now
- Updates top-level `severity_level`, `probability_level`, `risk_index`, `risk_level`
- Re-computes `risk_score = risk_index / 25`
- Returns full report

### GET /api/v1/reports/{id} — Extended response
Includes `risk_assessment` and `ai_suggested_assessment` in addition to existing fields.

### GET /api/v1/reports/ — Extended list response
Includes `risk_level` alongside existing `risk_score` and `severity`.

### GET /api/v1/dashboard/risk — Updated
Returns risk distribution grouped by `risk_level` (Low / Medium / High / Very High) instead of risk_score buckets. Falls back to severity-based grouping when risk_level is null.

### GET /api/v1/dashboard/caan/risk — Updated
Same grouping logic, aggregated across all tenants.

### GET /api/v1/admin/risk-matrix — New
**Auth:** SUPER_ADMIN. Returns current tenant's risk matrix config from metadata.

### PUT /api/v1/admin/risk-matrix — New
**Auth:** SUPER_ADMIN. Updates risk matrix thresholds/labels for a tenant.
**Body:** `{ thresholds?: {...}, severity_labels?: {...}, probability_labels?: {...} }`

---

## 3. Frontend Changes

### Report Form (mor.html)
Add two dropdown fields below the existing severity/likelihood fields:
- **Severity Level:** 1 (Negligible) … 5 (Catastrophic)
- **Probability Level:** 1 (Extremely Improbable) … 5 (Frequent)
- **Read-only computed:** Risk Index (1–25) + Risk Level badge

### Report Detail (if applicable)
- Panel showing: Severity Level, Probability Level, Risk Index, Risk Level, assessed_by, assessed_at
- "Confirm Assessment" button (visible to Safety Manager / AIRLINE_ADMIN)
- AI suggestion displayed separately with confidence score (not authoritative)

### Airline Dashboard (safety.html) — Risk Widget
- Replace risk_score-based distribution with risk_level distribution (Low / Medium / High / Very High)
- Add 5×5 risk heat-map chart showing count of reports in each cell (S × P)
- Color cells by risk_level threshold

### CAAN Dashboard — SSP Risk Heat Map
- Aggregate 5×5 across all tenants
- Show tenant-level drill-down on cell click

---

## 4. Migration Plan

### Step 1 — Schema + API (this milestone)
1. Add new nullable fields to Firestore via report service (no existing data changed)
2. Add `risk_assessment` confirmation endpoint
3. Add admin risk-matrix CRUD
4. Update dashboard queries to prefer `risk_level` over `risk_score`
5. Seed module generates both old and new fields
6. All legacy reports retain `risk_score` — dashboards fall back gracefully

### Step 2 — Frontend (this milestone)
1. Add severity/probability dropdowns to MOR form
2. Add risk assessment panel + confirm button to report view
3. Update dashboard risk charts

### Step 3 — AI integration (future)
1. Gemini/classifier suggests severity + probability
2. Stored in `ai_suggested_assessment` (never overwrites `risk_assessment`)
3. Safety Manager reviews and confirms (sets `risk_assessment`)

### Backward Compatibility Rules

| Scenario | Behavior |
|----------|----------|
| Old report, no new fields | `risk_index = null`. Dashboard uses `risk_score` (0.0–1.0). Risk levels derived from `severity` string if available. |
| New report, no assessment yet | `severity_level` + `probability_level` set from AI suggestion or user input. `risk_assessment = null`. Report appears in risk distribution based on provisional values. |
| Report with confirmed assessment | `risk_assessment` populated. All dashboard queries use the official values. |
| Seed data | Generated with both old fields (`risk_score`, `severity`, `likelihood`) and new fields (`severity_level`, `probability_level`, `risk_index`). |

### Seed Module Changes
- `risk_score` stays as-is (0.0–1.0)
- New: `severity_level` = mapped from severity string (Low→2, Medium→3, High→4, Critical→5)
- New: `probability_level` = mapped from likelihood string (Remote→2, Probable→4, Frequent→5)
- New: `risk_index` = severity_level × probability_level
- New: `risk_level` = derived from thresholds
- AI analysis suggests (not confirms) severity + probability in `ai_suggested_assessment`
- Per-tenant `risk_matrix` seeded with ICAO default

### No-Go Items (per Product Charter)
- Investigation management — NOT introduced
- Corrective action workflows — NOT introduced
- Risk matrix is assessment-only, does not trigger actions

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/core/config.py` | Add `RISK_MATRIX_DEFAULTS` settings |
| `backend/app/models/report.py` | Add `RiskAssessment`, `AiSuggestedAssessment` models; update `ReportResponse` |
| `backend/app/services/report_service.py` | Add `confirm_risk_assessment()`; update `create_report()` to accept new fields |
| `backend/app/services/risk_matrix.py` | NEW — `compute_risk_index()`, `get_risk_matrix()`, `get_risk_level()` |
| `backend/app/routes/reports.py` | Add `PUT /{id}/risk-assessment` endpoint |
| `backend/app/routes/admin.py` | Add `GET/PUT /risk-matrix` endpoints |
| `backend/app/services/dashboard_service.py` | Update risk distribution to use `risk_level` |
| `backend/app/services/metrics_service.py` | Update `calculate_risk_distribution()` for new levels |
| `backend/app/services/repository.py` | Add `risk_level` filter support |
| `backend/seed/config.py` | Add `risk_matrix` to tenant profiles |
| `backend/seed/reports.py` | Generate `severity_level`, `probability_level`, `risk_index`, `risk_level` |
| `backend/seed/operators.py` | Seed `risk_matrix` config in tenant metadata |
| `public/js/report.js` | Add severity/probability dropdowns to MOR form |
| `public/js/dashboard.js` | Update risk charts for new levels |
| `public/safety.html` | Add 5×5 risk heat-map |
| `backend/firestore.indexes.json` | Add composite index for `risk_level` + `occurrence_date` |
