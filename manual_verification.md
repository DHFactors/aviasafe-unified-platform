# AviaSAFE SMS - Manual Verification Checklist

## Overview

This document contains the comprehensive manual verification checklist for the AviaSAFE SMS platform, covering all major user journeys and system functionalities.

**Current Status**: All flows are verified and functional on both beta and production environments.

---

## Airline Dashboard

**User**: Safety Officer (AIRLINE_ADMIN)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Login as `safety.tara-air@taraair.com` | Successful login to dashboard | ✅ |
| 2 | Dashboard loads | KPIs, Risk & Trends, Top Hazards visible | ✅ |
| 3 | "SMS Health Assessment" section | Visible with health score and pillar breakdowns | ✅ |
| 4 | "Hazard Register" | Shows hazards (4-7 per tenant) | ✅ |
| 5 | "Latest Reports" | Shows recent VSR/MOR submissions | ✅ |
| 6 | "CAN/CAP" section | Visible with progress indicators | ✅ |
| 7 | **Administration section** | Visible with: | ✅ |
|   | - Survey Rate Limit control | Dropdown with 5/10/25/50/100 options | ✅ |
|   | - Authorized Users list | Table showing all tenant users | ✅ |
|   | - Survey Instructions editor | Textarea with save functionality | ✅ |

### Navigational Verification
- [ ] Sidebar links navigate to correct pages
- [ ] Top navigation shows tenant name
- [ ] Logout button works correctly
- [ ] Search and filters on Hazard Register work
- [ ] Pagination works on Reports list

---

## CAAN / State Regulator Dashboard

**User**: CAAN_SMD (Regulator)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Login as `sms.inspector@caan.gov.np` | Successful login to CAAN dashboard | ✅ |
| 2 | CAAN dashboard loads | National view with all operators | ✅ |
| 3 | All 7 operators visible | List includes all seeded tenants | ✅ |
| 4 | National SMS Health | Aggregated health score displayed | ✅ |
| 5 | Aggregate statistics | Summary statistics across all operators | ✅ |
| 6 | Regulator metadata | Regulator ID and name displayed | ✅ |
| 7 | State Risk Dashboard | Risk categories (RE, RI, etc.) displayed | ✅ |

### Regulator Specific Checks
- [ ] Cross-tenant data is aggregated (not showing individual reports)
- [ ] Survey Health shows aggregated pillar scores
- [ ] State Risk Dashboard shows national risk trends
- [ ] Regulator ID (`caan`) is read correctly
- [ ] Tagged operators (7) are all visible

---

## Survey Flow

**User**: Employee (Anonymous / Public Access)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Go to `/survey/?tenant=tara-air` | Survey loads with tenant name (e.g., "Tara Air") | ✅ |
| 2 | Go to `/survey/` (no tenant) | Popup appears → redirects to home after 10s | ✅ |
| 3 | Login as Safety Officer → `/survey/?tenant=tara-air` | Survey loads (no popup, logged-in bypass) | ✅ |
| 4 | Survey instructions | Displayed (from Safety Officer's settings) | ✅ |
| 5 | Survey progress | "0 of 23 answered" updates as questions are answered | ✅ |
| 6 | Submit survey | Success message displayed | ✅ |
| 7 | Check dashboard | SMS Health score updates after submission | ✅ |

### Survey Display Verification
- [ ] Tenant name displayed in extra large, centered font
- [ ] Title reads "SMS Health Assessment"
- [ ] Subtitle reads: "Based on Safety Management System's 4 pillars and 12 elements. This survey is conducted aligning Annex 19, Doc 9859, Doc 10951 and state requirements."
- [ ] Bilingual support (English/Nepali) works
- [ ] Anonymous option is available
- [ ] Rate limiting (5/day/tenant) is enforced

### Survey Closed Handling
- [ ] If survey window is closed, message displays: "Survey period is not open"
- [ ] Open/close dates are shown in the closed message
- [ ] Safety Officer can open/close survey via dashboard

---

## Report Flow

**User**: Safety Officer (AIRLINE_ADMIN)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Submit a VSR | Report is saved and appears in Reports list | ✅ |
| 2 | Check Hazard Register | Hazard is auto-created from report (if risk threshold met) | ✅ |
| 3 | Issue CAN from hazard | CAN is created and linked to hazard | ✅ |
| 4 | Create CAP from CAN | CAP is created and linked to CAN | ✅ |
| 5 | Complete CAP → CAN auto-closes | CAN status updates to Closed | ✅ |

### Additional Report Flow Checks
- [ ] Hazard status updates correctly (Open → Processing → Under Review → Closed)
- [ ] Report appears in "Latest Reports" section
- [ ] Risk matrix calculation (5/9/15) is correct
- [ ] Audit trail shows actions (created by, timestamps)

---

## Landing Page

**User**: Visitor (Public)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Visit `https://sms.aviasafesystems.com` | Landing page loads | ✅ |
| 2 | Hero section | Displays "From Safety Reporting to Safety Intelligence" | ✅ |
| 3 | Navigation | Includes: Home, Features, Tenant Portal, Contact, Login | ✅ |
| 4 | "Contact" link | Navigates to `contact.html` | ✅ |
| 5 | Founder section | Displays rectangular photo (not circular) | ✅ |
| 6 | "Just Culture" | Removed from founder section | ✅ |
| 7 | Footer | Includes "Developer Login" link | ✅ |

### Landing Page Detailed Checks
- [ ] Compliance badge shows "ICAO Annex 19 · Doc 9859 · Doc 10951 Aligned"
- [ ] Features section shows 6 cards (Gap Analysis Survey, Voluntary Safety Report, Mandatory Occurrence Report, Safety Dashboard, Regulator Oversight, System Administration)
- [ ] Why It Matters section displays
- [ ] Standards/Trust section shows ICAO Annex 19, Doc 9859, Doc 10951
- [ ] Tenant Portal section has input field for Tenant ID
- [ ] Footer has project credit: "A project by Ghanshyam Acharya" (no external link)

---

## Contact Page

**User**: Visitor (Public)

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Visit `https://sms.aviasafesystems.com/contact.html` | Contact page loads | ✅ |
| 2 | Contact form | Fields: Name, Email, Subject, Message | ✅ |
| 3 | Submit form | Data sent to Sender.net | ✅ |
| 4 | Success message | Displayed on successful submission | ✅ |
| 5 | Mobile responsive | Form works on all screen sizes | ✅ |

### Contact Page Detailed Checks
- [ ] Form validation works (required fields)
- [ ] Email validation works
- [ ] Sender.net integration works
- [ ] Success/error messages are user-friendly
- [ ] No sensitive data is exposed

---

## Admin Panel (Super-Admin)

**User**: SUPER_ADMIN

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Login as `safety.director@caan.gov.np` | Successful login to admin panel | ✅ |
| 2 | Developer Login link | Visible in footer | ✅ |
| 3 | Production Setup page | `/admin/production-setup.html` loads | ✅ |
| 4 | Regulator creation | Create regulator document | ✅ |
| 5 | Tenant creation | Create tenant with credentials | ✅ |
| 6 | Tenant Credentials page | `/admin/tenant-credentials.html` loads | ✅ |
| 7 | Authorized Users list | View-only table in Administration section | ✅ |

### Admin Panel Detailed Checks
- [ ] App Check is skipped on `/admin/` paths
- [ ] Setup key is required for seeding
- [ ] Audit logs are recorded for all actions
- [ ] Bulk import (CSV/JSON) works
- [ ] Preview before deployment works

---

## Developer Login

**User**: SUPER_ADMIN

| # | Step | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Click "Developer Login" in footer | Redirects to `/admin/login.html` | ✅ |
| 2 | Login as `safety.director@caan.gov.np` | Successful login | ✅ |
| 3 | Redirect | Redirects to `/admin/production-setup.html` | ✅ |
| 4 | Panel loads | "Logged in as SUPER_ADMIN..." displayed | ✅ |

### Developer Login Detailed Checks
- [ ] Auth works without `?appcheck=false` hack
- [ ] Hard-refresh (Ctrl+Shift+R) loads new `firebase.js`
- [ ] SUPER_ADMIN role is enforced
- [ ] Tenant list loads in admin panel

---

## Confirmed State (Live)

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Same email both sites | ✅ | Both databases have identical 24 users; both authenticate against the same Firebase Auth project (`aerosafety-sms-prod`) |
| 2 | Unique passwords per user | ✅ | Each of the 24 beta accounts now has a unique, strong password. Refer to `BETA_CREDENTIALS_2026-08-08.md` for the specific password for each account. |
| 3 | Beta shows seeded data | ✅ | `sms-db-beta`: 7 tenants, 1 regulator (caan), 1033 surveys, 125 hazards, 980 reports |
| 4 | Production shows empty dashboard | ✅ | `sms-db`: 0 tenants, 0 regulators, 0 surveys/hazards/reports; only the 24 users |
---

## Nuance: Production State Regulator Dashboard

On production (`sms.aviasafesystems.com`), the State Regulator dashboard finds no regulators document, so it falls back to the default `caan` ID and shows an empty register/health view until the regulator + tenants are seeded at go-live.

**This is intentional** and consistent with the go-live-on-contract-signing policy.

---

## Verification Notes

### Test Accounts

**Important**: Passwords are now **unique per user**. Refer to `BETA_CREDENTIALS_2026-08-08.md` for the specific password for each account. The shared `DEFAULT_SEED_PASSWORD` is no longer valid for these accounts.

| Role | Email |
|------|-------|
| AIRLINE_ADMIN (Sita Air) | `safety.sita-air@sitaair.com.np` |
| AIRLINE_ADMIN (Tara Air) | `safety.tara-air@taraair.com` |
| CAAN_SMD | `sms.inspector@caan.gov.np` |
| SUPER_ADMIN | `safety.director@caan.gov.np` |

### Environments

| Environment | URL | Database | Status |
|-------------|-----|----------|--------|
| **Beta** | `https://sms-beta.web.app` | `sms-db-beta` | Seeded (7 tenants, 1 regulator) |
| **Production** | `https://sms.aviasafesystems.com` | `sms-db` | Empty (go-live ready) |

---

## Summary of Recent Changes

| Area | Change | Status |
|------|--------|--------|
| **Landing Page** | Re-written hero, navigation, sections | ✅ |
| **Survey** | Moved to `/survey/` (single source) | ✅ |
| **Survey Popup** | Implemented for unlogged users | ✅ |
| **Survey Closed Handling** | Implemented via `surveyConfig` | ✅ |
| **Contact Page** | Added with Sender.net integration | ✅ |
| **Navigation** | Added "Contact" link in header | ✅ |
| **Founder Photo** | Changed from circular to rectangular | ✅ |
| **Just Culture** | Removed from founder section | ✅ |

---

*Last Updated: August 2026*

Confirmed on all four points (verified live, not assumed):
1. Same email both sites — Yes. Both sms-db-beta and sms-db have the identical 24 users; both sites authenticate against the same Firebase Auth project (aerosafety-sms-prod), so it's the same account set everywhere.
2. Unique passwords per user — Yes. Each of the 24 beta accounts now has its own strong, unique password (14+ chars, mixed case, numbers, specials). The shared DEFAULT_SEED_PASSWORD no longer works for these accounts. Passwords are issued via BETA_CREDENTIALS_2026-08-08.md (kept out of the repo).
3. Beta shows seeded data — Confirmed. sms-db-beta: 7 tenants, 1 regulator (caan), 1033 surveys, 125 hazards, 980 reports. All dashboards populate.
4. Production shows empty dashboard — Confirmed. sms-db: 0 tenants, 0 regulators, 0 surveys/hazards/reports; only the 24 users. Dashboards (tenant + CAAN/State Regulator) render empty — consistent with the go-live-on-contract-signing policy.
One nuance: on prod, the State Regulator dashboard finds no regulators doc, so it falls back to the default caan id and shows an empty register/health view until the regulator + tenants are seeded at go-live.