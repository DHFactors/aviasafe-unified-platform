# Aviasafe Demo Guide — ICAO SMS Platform

## Prerequisites

1. Firestore emulator running + Firebase Auth emulator seeded
2. Backend running on `localhost:8080`
3. Frontend Hosting emulator on `localhost:5000`
4. All seed users created (`python -m seed.run`)

## User Matrix (password: `Demo@123456`)

| Role | Example Email | Tenant Scope |
|------|--------------|--------------|
| **SUPER_ADMIN** | `safety.director@caan.gov.np` | System-wide |
| **CAAN_SMD** | `sms.inspector@caan.gov.np` | Cross-tenant (regulator) |
| **AIRLINE_ADMIN** | `safety.buddha_air@buddhaair.com` | `buddha_air` |
| **USER** | `manager.buddha_air@buddhaair.com` | `buddha_air` (read-only submit) |

Use any operator from the 6 profiles: `buddha_air`, `yeti_airlines`, `summit_air`, `sita_air`, `air_dynasty`, `simrik_air`.

---

## Demo Flow (recommended order)

### 1. USER — Report Submission *(2 min)*

**Login:** `manager.buddha_air@buddhaair.com` / `Demo@123456`

- Land on **airline dashboard** (`/`) — sees reports list (read-only, no edit controls)
- Click **"Submit Report"** → choose **MOR** (Mandatory Occurrence Report)
- Fill narrative, location, occurrence date
- **Key demo moment:** Set Severity = `3` and Probability = `3` → submit
- Back on dashboard → new report appears with `risk_index = 9 (3×3)`, `risk_level = Medium`
- Show that **"Confirm Risk Assessment" button is absent** — USER cannot override
- Submit a **VSR** (Voluntary) report too — note the anonymous toggle

**Client talking points:**
- "Any employee can report safety concerns with ICAO severity/probability"
- "Anonymous reporting option encourages safety culture"
- "Risk index auto-calculated per ICAO Doc 9859"

---

### 2. AIRLINE_ADMIN — Safety Management *(5 min)*

**Login:** `safety.buddha_air@buddhaair.com` / `Demo@123456`

**a) Dashboard overview**
- Reports table with risk_index, risk_level, severity_level, probability_level columns
- **5×5 heat map** — click any cell to filter reports at that severity×probability intersection
- Risk level distribution bar chart

**b) AI Analysis (click a report row → detail page)**
- Navigate to `/report/detail.html?id=<report_id>`
- Shows **AI Assistant panel** with:
  - Suggested severity (1-5) + probability (1-5) with ICAO-grounded explanations
  - Example: "Severity 4 — hazardous, life-threatening injuries per NTSB precedent"
  - AI confidence score
- **Key demo moment:** The AI references real aviation precedents (NTSB, EASA)

**c) Safety Manager Override (the ICAO lifecycle)**
- In detail page, safety manager section: set Severity = `4`, Probability = `4`, add notes
- Click **"Confirm Risk Assessment"**
- Page updates: official `risk_index = 16`, `risk_level = Very High`
- **"OFFICIAL" badge** appears — AI suggestion preserved alongside for audit trail

**d) Risk Matrix Configuration**
- Dashboard → **Risk Matrix Settings** section
- Adjust thresholds: `low_max`, `medium_max`, `high_max`
- Show how changing `high_max` from 15 → 20 changes risk_index=16 from "Very High" → "High"
- Save — config persists per tenant

**Client talking points:**
- "Full ICAO 5×5 risk matrix with tenant-isolated configuration"
- "AI provides grounded suggestions but safety manager always holds authority"
- "Before/after audit trail — AI suggestion + official assessment preserved"

---

### 3. CAAN_SMD — Regulatory Oversight *(3 min)*

**Login:** `sms.inspector@caan.gov.np` / `Demo@123456`

**a) Regulator Dashboard (`/caan.html`)**
- Cross-tenant view of all operators' reports
- **Risk level bar chart** — aggregate across all 6 airlines
- **5×5 heat map** — computed from all tenants' severity/probability fields
- Industry summary table showing High Risk / Very High Risk counts per operator

**b) Drill into any airline's report**
- Click a report → detail page with AI panel
- CAAN_SMD can confirm risk assessment across any tenant (cross-tenant authority)

**c) Risk Matrix visibility**
- Can view each airline's risk matrix config (but CAAN dashboard handles aggregation)

**Client talking points:**
- "Regulator sees a unified picture across all operators"
- "Can intervene by confirming/rejecting any airline's risk assessments"
- "Industry-wide heat map reveals systemic safety trends"

---

### 4. SUPER_ADMIN — System Administration *(2 min)*

**Login:** `safety.director@caan.gov.np` / `Demo@123456`

- Full access to all endpoints (cross-tenant)
- Admin panel at `/admin/`:
  - User management, system config
  - Can confirm risk assessments for any report in any tenant
- **Key distinction:** SUPER_ADMIN is CAAN's top-level director; CAAN_SMD is the operational SMS inspectorate

**Client talking points:**
- "SUPER_ADMIN has the final system-wide authority"
- "Separation between operational oversight (CAAN_SMD) and system ownership (SUPER_ADMIN)"

---

## ICAO Risk Assessment Lifecycle — Complete Walkthrough

This is the **core demo** — run this sequence to show the full value:

| Step | Action | Result |
|------|--------|--------|
| 1 | USER submits MOR with S=3, P=3 | `risk_index=9`, `risk_level=Medium` |
| 2 | (Background) AI analyzes narrative | `ai_suggested_assessment` with S=4, P=2, explanations |
| 3 | AIRLINE_ADMIN opens detail page | Sees AI suggestion + grounding (NTSB/EASA references) |
| 4 | AIRLINE_ADMIN overrides to S=4, P=4 | Official `risk_index=16`, `risk_level=Very High` |
| 5 | Both records stored | AI suggestion preserved; official assessment marked |
| 6 | CAAN_SMD views cross-tenant | Sees the assessment in regulator dashboard |

---

## Quick Credential Reference Card

```
SUPER_ADMIN:   safety.director@caan.gov.np       / Demo@123456
CAAN_SMD:      sms.inspector@caan.gov.np          / Demo@123456
               director.safety@caan.gov.np        / Demo@123456

Buddha Air:
  AIRLINE_ADMIN:  safety.buddha_air@buddhaair.com / Demo@123456
  AIRLINE_ADMIN:  ae.buddha_air@buddhaair.com     / Demo@123456
  USER:           manager.buddha_air@buddhaair.com / Demo@123456

Yeti Airlines:
  AIRLINE_ADMIN:  safety.yeti_airlines@yetiairlines.com / Demo@123456
  USER:           manager.yeti_airlines@yetiairlines.com / Demo@123456

Summit Air:       safety.summit_air@summitair.com.np / Demo@123456
Sita Air:         safety.sita_air@sitaair.com.np     / Demo@123456
Air Dynasty:      safety.air_dynasty@airdynasty.com.np / Demo@123456
Simrik Air:       safety.simrik_air@simrikair.com    / Demo@123456
```
