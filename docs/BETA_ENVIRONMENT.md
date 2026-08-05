# AviaSAFE SMS — Beta Environment Setup Notes

Versioned reference for the closed-beta environment. Verified **2026-08-05**.

## Overview

The beta is a fully isolated environment that mirrors production. Beta traffic can never touch production data.

| Component | Beta | Production |
|-----------|------|------------|
| **Hosting** | `https://sms-beta.web.app` (site `sms-beta`, project `gap-analysis-ssp`) | `sms.aviasafesystems.com` / `aerosafety-sms-prod.web.app` |
| **Backend** | `https://sms-aviasafesystems-beta.onrender.com` | `https://aviasafe-unified-platform.onrender.com` |
| **Firestore** | `sms-db-beta` (native, us-west1, project `aerosafety-sms-prod`) | `sms-db` (native, us-west1) |
| **Redis** | Upstash `aviasafe-redis` (rate limiting) | Not used |

Frontend routing (`public/js/firebase.js`) selects beta config by hostname containing `beta`:
`databaseId: "sms-db-beta"`, `apiBaseUrl: "https://sms-aviasafesystems-beta.onrender.com"`, `environment: "beta"`.

## Firestore PITR — Verified Retention (sms-db-beta)

Verified with:

```
gcloud firestore databases describe --database=sms-db-beta
```

Key output:

```
pointInTimeRecoveryEnablement: POINT_IN_TIME_RECOVERY_ENABLED
versionRetentionPeriod: 604800s        # = 7 days
earliestVersionTime: '2026-08-05T02:18:00Z'
locationId: us-west1
type: FIRESTORE_NATIVE
```

**Result:** PITR is enabled with a **7-day retention** (`versionRetentionPeriod: 604800s`). This is already the maximum — no change required (the 1-day default did not apply).

### Reference: forcing 7-day retention (not needed, documented for completeness)

```
gcloud firestore databases update --database=sms-db-beta --enable-pitr --retention-duration=7d
```

`versionRetentionPeriod` is read after the update to confirm `604800s`.

## Deployment Notes

- `backend/render.yaml` configures the production Docker service; the beta Render service (`sms-aviasafesystems-beta`) is managed from the Render dashboard with `FIREBASE_DATABASE_ID=sms-db-beta`.
- Beta service env vars: `REDIS_URL` (Upstash), `ALLOWED_ORIGINS` must include `https://sms-beta.web.app`, `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL`, `GEMINI_API_KEY`, `DEBUG=false`.
- Firestore security rules and indexes are shared with production and deployed from `backend/firestore.rules` / `backend/firestore.indexes.json`.

## Verification Commands

```bash
# Backend liveness
curl https://sms-aviasafesystems-beta.onrender.com/live

# Firestore PITR state
gcloud firestore databases describe --database=sms-db-beta

# Redis rate-limit keys (from a machine with redis access)
# expect rl:<type>:<tenant|ip>:<period> keys while active
```

## Related Documents

- `docs/BETA_TEST_CHECKLIST.md` — tester checklist
- `docs/BETA_INVITATION_TEMPLATE.md` — tester invitation email
- `docs/FEEDBACK_FORM_STRUCTURE.md` — feedback form fields
