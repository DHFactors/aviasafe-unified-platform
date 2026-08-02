# AviaSAFE Release Notes — RC-5

**Release:** Release Candidate 5 (RC-5) — Operational Pilot Readiness
**Date:** 02 August 2026
**Version:** API 1.0.0
**Deployment candidate:** Repository state at commit `4e306ce` + RC-1→RC-5 working-tree changes
(backend Docker image built from `backend/Dockerfile`, Python 3.11)
**Status:** READY FOR RC-6 – PRODUCTION READINESS REVIEW (conditional upon successful Render
deployment — see Pending Operator Actions in `PROJECT_STATUS_REPORT_02AUG2026.md`)

---

## 1. What Changed from RC-1 through RC-5

### RC-1 — Security Hardening & Release Blockers
- Removed hardcoded `SETUP_SECRET`; moved to env (`SETUP_SECRET`) and made it a **second factor** —
  every admin endpoint now requires a SUPER_ADMIN Firebase ID token (`Depends(get_admin_user)`),
  fail-closed (503) when the secret is unset.
- Removed open debug endpoints `/check-data`, `/debug-verify`, `/migrate-seed-data`; gated
  `/seed-demo-data` and `/create-seed-users` behind `DISABLE_DESTRUCTIVE_ENDPOINTS` (default true).
- Purged plaintext credentials from source and provisioning scripts (env-driven passwords).
- Fixed `PUT /risk-matrix` crash (passes `updated_by`).

### RC-2 — Functional Corrections & Regression Validation
- Unified the ICAO 5×5 risk matrix: one canonical, configurable scheme
  (`get_risk_level`/`get_thresholds`) used by reports, hazards, dashboards, AI suggestions, and
  seed; stored tenant thresholds now honoured by scoring; frontend hazard preview aligned.
- Removed duplicate/dead risk logic; fixed `risk_matrix_config.updated_at` to Firestore Timestamp.
- Added `test_risk_matrix.py` (16 tests) → suite 24 → 40.

### RC-3 — Documentation & Operational Readiness
- Full documentation suite: README, ARCHITECTURE, INSTALLATION, DEPLOYMENT, OPERATIONS, ADMIN_GUIDE,
  API (verified route inventory), SECURITY (rewritten to the actual model), KNOWN_LIMITATIONS,
  HAZARD_TAXONOMY; tenant-guide steps 01–03; `.env.example`.
- Purged remaining plaintext credentials from docs; corrected stale route/version counts.

### RC-4 — UAT Readiness (Independent IV&V)
- Executed UAT across all 12 areas; 12 findings recorded (`UAT_DEFECT_REGISTER.md`), **8 fixed**:
  - UAT-001 (Critical): CAAN/SuperAdmin risk-assessment confirmation cross-tenant.
  - UAT-002 (High): CAAN cross-tenant CAP reads + CAP-list response model (500 fix).
  - UAT-003 (High): reporting `tenant_id` override restricted to cross-tenant roles.
  - UAT-004 (High): anonymous survey unblocked (client `tenantId` + rule alignment).
  - UAT-005 (Critical, deployment): live build lacks admin bearer auth → re-deploy required.
  - UAT-006 (Medium): reportlab added to requirements; valid PDF verified.
  - UAT-007 (High): cross-tenant write guards (CAN/CAP/verification/closure/diversions).
  - UAT-008 (Medium): test mocks corrected; cross-tenant regression coverage added.
- Regression: 40 → 46 tests passing.

### RC-5 — Operational Pilot Readiness (this release)
- Validated the deployable artifact (Docker build, boot, auth enforcement, PDF generation,
  46/46 tests).
- Verified the full production environment, operational procedures, pilot airline onboarding
  workflow, and monitoring readiness.
- Produced `PILOT_READINESS_REPORT.md` and this release-notes artifact.
- Recorded the Render deployment as a Pending Operator Action (UAT-005).

## 2. Security Improvements

- Admin surface requires SUPER_ADMIN Bearer + env setup key (no hardcoded secret).
- Debug/destructive endpoints closed in the candidate build (`DISABLE_DESTRUCTIVE_ENDPOINTS`).
- Cross-tenant authorization defects fixed (reporting override, CAN/CAP/verification writes).
- `secrets.compare_digest` constant-time key comparison.
- Security headers (HSTS, nosniff, frame-deny, XSS, referrer, permissions-policy) + Hosting headers.
- No plaintext credentials in code (grep-verified).
- Remaining (documented): server-side App Check not enforced (TD-12); MFA not enforced.

## 3. Functional Improvements

- CAAN cross-tenant reporting and CAP visibility operational.
- Anonymous survey submissions unblocked and rules-aligned.
- Canonical, configurable risk matrix across all surfaces.
- Valid PDF report export (reportlab shipped in requirements).
- Tenant-required guards prevent phantom-tenant data corruption.

## 4. Documentation Completed

- `README.md`, `docs/ARCHITECTURE.md`, `docs/INSTALLATION.md`, `docs/DEPLOYMENT.md`,
  `docs/OPERATIONS.md`, `docs/ADMIN_GUIDE.md`, `docs/API.md`, `docs/SECURITY.md`,
  `docs/KNOWN_LIMITATIONS.md`, `docs/HAZARD_TAXONOMY.md`, `docs/ONBOARDING_CREDENTIALS_20_AIRLINES.md`,
  `public/docs/tenant-guide/` steps 01–03, `backend/.env.example`.
- UAT deliverables: `UAT_DEFECT_REGISTER.md`, `UAT_EXECUTION_REPORT.md`.
- This release: `PILOT_READINESS_REPORT.md`, `RELEASE_NOTES_RC5.md`.

## 5. UAT Outcomes

- 12 findings: 8 fixed & verified, 1 deployment action (UAT-005), 3 recommendations, 1 deferred
  (UAT-012 closure-ordering).
- Regression suite: **46/46 passed**.
- See `UAT_DEFECT_REGISTER.md` and `UAT_EXECUTION_REPORT.md` for full detail.

## 6. Known Limitations

- Live backend is still the pre-hardening build until the operator re-deploys (UAT-005).
- Survey is not yet charter-aligned (4 components / 12 elements) — TD-6.
- Server-side App Check not enforced; public VSR/response create is a spam surface — TD-12.
- No automated Firestore backups / PITR enabled.
- No dedicated staging environment (staging shares production Firestore).
- AI risk suggestions are heuristic; official assessment is always human-confirmed.
- No notifications service.
- `/docs` exposed in production (UAT-009, recommendation).

## 7. Outstanding Technical Debt

| ID | Item |
|----|------|
| TD-6 | Survey charter re-alignment (4 components / 12 elements) |
| TD-7 | `public/portal` mock code removal |
| TD-8 | No CI/CD; two `render.yaml`; service-name mismatch |
| TD-10 | Firestore indexes camelCase vs snake_case drift |
| TD-12 | Server-side App Check / public-create spam control |
| TD-15 | `seed_metadata.seeded_at` ISO string leftover |
| — | Self-registration accepts arbitrary `tenant_id` |
| — | Redis `ssl_cert_reqs=CERT_NONE` |
| — | `survey_submit`/`dashboard` rate-limit definitions not attached |
| — | Stale provisioning curl example in `docs/OPERATIONS.md` |

## 8. Pilot Deployment Prerequisites

1. **Operator:** trigger Render re-deploy of the RC-5 candidate (service `aviasafe-unified-platform`,
   Docker path `backend/Dockerfile`).
2. **Operator:** set/confirm Render env vars (`SETUP_SECRET`, `DEFAULT_PROVISION_PASSWORD`,
   `DEFAULT_SEED_PASSWORD`, `DEBUG=false`, `DISABLE_DESTRUCTIVE_ENDPOINTS=true`, `ALLOWED_ORIGINS`,
   Firebase + Gemini + `REDIS_URL`).
3. **Verify:** live OpenAPI shows `security: [{"HTTPBearer":[]}]` on admin endpoints; legacy
   `/check-data`/`/migrate-seed-data` gone; `/health` firebase connected.
4. **Smoke test:** health/live/ready, auth (401 invalid token), protected surfaces (403), one VSR +
   one MOR, dashboard, risk-matrix, report generation.
5. **Enable:** Firestore Backups/PITR (data-protection for pilot).
6. **Decide:** self-registration policy (recommend disabling or domain-validation during pilot).
7. **Document:** deployment timestamp + deployed commit hash; confirm production matches the
   validated repository.

---

*End of release notes. RC-6 (Production Readiness Review) begins only after stakeholder approval and
completion of the Pending Operator Actions.*
