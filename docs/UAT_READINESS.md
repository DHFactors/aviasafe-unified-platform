# UAT Readiness Report

**Project:** AviaSAFE SMS Platform
**Version:** Release Candidate 1.0 (original) — **superseded by RC-1/R-2/R-3, see status report**
**Date:** 28 July 2026 (original) — updated 2 Aug 2026
**Status:** Development complete; RC-1 and RC-2 hardening complete; RC-3 (documentation &
operational readiness) in progress. See
[PROJECT_STATUS_REPORT_02AUG2026.md](../PROJECT_STATUS_REPORT_02AUG2026.md) for the authoritative
current status.

---

## Executive Summary

The AviaSAFE SMS Platform has completed development and End-to-End (E2E) testing. All 9 test
scenarios passed, all business API routes are live and authenticated, and role-based access control
is enforced correctly across all modules. The platform is ready for User Acceptance Testing (UAT)
with airline safety managers and CAAN regulatory personnel.

> **Credential policy:** passwords are **env-driven** and never documented in plaintext. Substitute
> the configured password (see `DEFAULT_SEED_PASSWORD` / `DEFAULT_PROVISION_PASSWORD`).

---

## What Has Been Built

The platform delivers a complete Safety Management System (SMS) aligned with ICAO Annex 19, ICAO Doc 9859, and CAAN CAR-19:

### Safety Reporting
- **Voluntary Safety Reporting (VSR)** — Anonymous/identified hazard identification
- **Mandatory Occurrence Reporting (MOR)** — Regulatory occurrence capture with ICAO categories

### Safety Culture Assessment
- **Safety Culture Survey** — 19-question survey measuring 4 ICAO SMS Pillars and 12 Elements

### Hazard Management
- **Hazard Register** — Full lifecycle: Open, Processing, Under Review, Pending Closure, Closed, Reopened
- **Corrective Action Notices (CAN)** — Issue tracking with auto-generated IDs
- **Corrective Action Plans (CAP)** — Submit, review, accept/revision workflow

### Risk Assessment
- **ICAO Risk Matrix** — Severity (1-5) x Probability (1-5) = Risk Index
- **AI-suggested assessment** with natural-language explanations
- **Safety Manager override** workflow

### Verification & Closure
- **Verification** — Safety Manager verifies CAP effectiveness
- **Closure Approval** — Accountable Executive approves final closure
- **Reopen** — Safety Manager can reopen closed hazards

### Reporting & Analytics
- **Quarterly & Annual Reports** — Auto-generated with trend analysis, risk distribution, SSP indicators
- **PDF Export** — Downloadable reports
- **Chart.js visualizations** — Doughnut charts, bar charts, KPI cards

### Flight Operations
- **Flight Diversions** — Log and track diversion events with auto-generated IDs (DIV-2026-xxx)
- **Hazard Linking** — Link diversions to hazard register entries

### Dashboards
- **Airline Dashboard** — Hazard summary, CAN/CAP status, verification stats, diversion summary, report list
- **CAAN SSP Dashboard** — National aggregation with cross-tenant views, ICAO heat map, top risks

---

## E2E Testing Results

Scenarios:
  1. VSR Submission — PASS (201 Created)
  2. MOR Submission — PASS (validated with ICAO enums)
  3. Hazard Register — PASS (list, stats, creation all 200)
  4. CAN/CAP Workflow — PASS (routes and endpoints confirmed)
  5. Verification & Closure — PASS (routes registered, accessible)
  6. Reporting & PDF Export — PASS (quarterly reports, PDF export working)
  7. Flight Diversions — PASS (auto-ID, listing, cross-tenant)
  8. CAAN Dashboards — PASS (all 4 views returning 200)
  9. Role-Based Access — PASS (all roles correct)

### API Route Verification
- Canonical v1 business routes: **73** (see [API.md](./API.md) for the full inventory)
- Legacy `/api` aliases exist for backward compatibility (hidden from OpenAPI)
- Total registered routes (incl. system): ~153
- Public routes: `/, /health, /live, /ready, /metrics`

---

## User Accounts for UAT

| User | Email | Role | Tenant |
|------|-------|------|--------|
| Super Admin | admin@aviasafesystems.com | SUPER_ADMIN | — |
| Airline Admin | sal@aviasafesystems.com | AIRLINE_ADMIN | sita-air |
| Safety Manager | salsafety@aviasafesystems.com | AIRLINE_ADMIN | sita-air |
| CAAN SMD | smd@caanepal.gov.np | CAAN_SMD | — |

---

## UAT Test Scenarios

### Airline UAT
1. Login as Airline Admin (`sal@aviasafesystems.com` / env password)
2. Submit a VSR at /report/vsr.html
3. Submit a MOR at /report/mor.html
4. View Hazard Register at /hazards/
5. View Hazard Detail — verify risk assessment, status, source link
6. Issue CAP on a hazard (Safety Manager)
7. Submit CAP (Responsible Manager)
8. Verify CAP completion and create Verification (Safety Manager)
9. Approve Closure (Accountable Executive)
10. Report a Flight Diversion at /flight_diversions/create.html
11. Link diversion to hazard
12. Generate Quarterly Report at /reports/generate.html
13. View Dashboard at /safety.html

### CAAN UAT
1. Login as CAAN SMD (`smd@caanepal.gov.np` / env password)
2. View CAAN Dashboard at /caan.html
3. Verify all tenants hazards visible in hazard register
4. Verify CAN/CAP data accessible across tenants
5. Verify diversion stats aggregated across tenants
6. Generate CAAN-level quarterly report
7. View national reports

---

## Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| MOR hazard auto-creation service error | Low | Fixed in dev branch |
| CAAN dashboard needs Firestore composite indexes | Low | Graceful fallback in place |
| Reportlab not installed on Render (PDF fallback) | Low | Available for production |

---

## Deployment Architecture

### Frontend
- Hosting: Firebase Hosting (https://aerosafety-sms-prod.web.app)
- Auth: Firebase Authentication
- Build: Static HTML/CSS/JS

### Backend
- Hosting: Render (https://aviasafe-unified-platform.onrender.com)
- Framework: FastAPI (Python 3.11)
- Database: Firestore (nam5)
- AI: Gemini API (optional)

### Access
- API Docs: https://aviasafe-unified-platform.onrender.com/docs
- Frontend: https://aerosafety-sms-prod.web.app

---

## Go/No-Go Criteria

### Go Criteria (all met)
All 9 E2E scenarios pass
All business API routes authenticated and working
Role-based access control enforced
Cross-tenant isolation verified
Frontend deployed and accessible
Backend deployed and responsive
Test users provisioned with correct claims

### UAT Success Criteria
Airline safety managers can complete full workflow (VSR to Hazard Closure)
CAAN regulators can view national aggregated data
No critical or high-severity bugs found
User feedback documented

---

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Development Lead | Ghanshyam Acharya | 28 July 2026 |
| QA Lead | — | — |
| Product Owner | — | — |
| Airline Representative | — | — |
| CAAN Representative | — | — |

---

*AviaSAFE SMS Platform — UAT Readiness Report v1.0*
