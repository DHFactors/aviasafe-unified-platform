# Migration Checklist — New Firebase/GCP Project

> **Purpose:** Migrate the AviaSAFE SMS Platform off the broken `gap-analysis-ssp`
> project (Auth stuck in `PROJECT_SOFT_DELETED` after project undelete) onto a
> fresh Google Cloud project with a new $300 credit billing account.
>
> **Status:** `COMPLETE` — live platform fully verified on new project `aerosafety-sms-prod`
>
> **Date started:** 2026-08-04
>
> **Progress log (2026-08-04):**
> - New project **`aerosafety-sms-prod`** (527947363983) created and linked to Firebase; web app exists.
> - Firestore named DB **`sms-db`** created (us-west1); typo DB `smd-db` deleted.
> - Auth **Email/Password** enabled; `sms.aviasafesystems.com` added to authorized domains.
> - Service account key generated (stored out-of-repo; loaded into local `backend/.env`).
> - Repo config switched to the new project (commit `578a3d8`, pushed): web configs, hosting site,
>   `.firebaserc`, CORS `ALLOWED_ORIGINS`, E2E API keys, docs.
> - Hosting + Firestore rules/indexes deployed to `aerosafety-sms-prod`; new site HTTP 200.
> - Custom domain provisioned on the new hosting site (`CERT_ACTIVE`); DNS CNAME switch **done**.
> - **Seed complete** on `sms-db`: 6 tenants, 930 surveys, 620 VSR, 245 MOR, 21 Auth users (incl.
>   SUPER_ADMIN `safety.director@caan.gov.np`). Login verified (new API key).
> - **Render env updated + redeployed** by operator (`FIREBASE_*`, `DEFAULT_SEED_PASSWORD`,
>   `ALLOWED_ORIGINS` incl. custom domain). `/health` healthy/connected.
> - **Full end-to-end verification passed** (2026-08-04): login (SUPER_ADMIN/CAAN_SMD/AIRLINE_ADMIN),
>   protected `/api/v1/admin/risk-matrix` 200, `/api/v1/reports/` 280 tenant reports,
>   CORS preflight + `Access-Control-Allow-Origin` from `sms.aviasafesystems.com`, custom domain serves
>   new site HTTP 200. Migration **COMPLETE**.

---

## 1. Why we are migrating

| Symptom | Root cause |
|---|---|
| `POST accounts:signInWithPassword` → HTTP 400 `PROJECT_SOFT_DELETED` | Firebase Auth (Identity Toolkit) stuck in soft-deleted state after project restore; known Google issue (firebase-js-sdk#10040, firebase-tools#10603). Only Google Support reconciles it — no client-side workaround. |
| Firestore `(default)` writes → 400 "database was deleted" | Same undelete transition; worked around by creating named database `sms-db` (already live + wired). |
| Firestore `(default)` create → 409, delete → 404 | Tombstoned GCP state, unresolvable from client side. |

Seeding, logins, and Auth user provisioning are all blocked until Auth is healthy.
A fresh project eliminates the entire problem and adds free-credit headroom.

---

## 2. Operator steps (manual, in the consoles)

- [x] **A. Create GCP project**
  - Log into Google Cloud Console with the $300-credit account.
  - Click project dropdown → **New Project**.
  - Suggested name/ID: `aerosafety-sms-prod` (or chosen ID).
- [x] **B. Link to Firebase**
  - Open [Firebase Console](https://console.firebase.google.com).
  - **Add project** → *Import Google project* → select the project from step A.
  - This binds the $300 billing profile automatically.
- [x] **C. Enable services**
  - **Authentication** → Sign-in method → enable **Email/Password**.
  - **Firestore Database** → create database named **`sms-db`** (choose a region, e.g. `us-west1` like before, or `nam5`).
  - (Optional) **App Check**, **Storage** — only if needed.
- [x] **D. Create Firebase web app** (for the frontend)
  - Project Settings → Your apps → Add web app (`</>`).
  - Copy the web SDK config: `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`.
- [x] **E. Generate service account key**
  - Project Settings → Service accounts → **Generate new private key**.
  - Save the JSON securely. Used for `FIREBASE_PRIVATE_KEY` + `FIREBASE_CLIENT_EMAIL` on Render / local `.env`.
- [x] **F. Re-link custom domain**
  - Firebase Hosting → **Add custom domain** → `sms.aviasafesystems.com`.
  - Update DNS as prompted (will re-provision SSL).
  - Note: `gap-analysis-ssp.web.app` will no longer serve; the new default is `<new-id>.web.app`.

---

## 3. Files to update (repo) — I can do this once you paste the new config

New values needed:
- [x] New **project ID** (from step A / D)
- [x] New **web app config** (from step D)
- [x] New **service account** email + private key (from step E)

| File | Change |
|---|---|
| `public/js/firebase.js` | Replace `firebaseConfig`: `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`. Keep `databaseId: "sms-db"`. |
| `public/portal/survey/app.js` | Same web config replacement. |
| `public/portal/dashboards/caan.js` | Same web config replacement. |
| `public/portal/dashboards/dashboard.js` | Same web config replacement. |
| `firebase.json` | `"site": "gap-analysis-ssp"` → new hosting site name. |
| `.firebaserc` | `"smssurvey": "gap-analysis-ssp"` → new project ID. |
| `backend/render.yaml` | `FIREBASE_PROJECT_ID` (sync:false), `ALLOWED_ORIGINS` (`*.web.app` → new), keep `FIREBASE_DATABASE_ID=sms-db`. |
| `backend/app/core/config.py` | `ALLOWED_ORIGINS` default → new `.web.app` + `sms.aviasafesystems.com`. |
| `backend/.env.example` | `ALLOWED_ORIGINS` example; note new service-account fields. |
| `docs/DEPLOYMENT.md`, `docs/ARCHITECTURE.md`, `README.md`, `PROJECT_STATUS.md`, `PROJECT_STATUS_REPORT_02AUG2026.md`, others | Project ID + hosting URL references (docs only). |

> **Caution:** do NOT change `databaseId: "sms-db"` — the named database is intentional and survives the project migration.

---

## 4. Environment variables (Render + local)

- [x] **Local** `backend/.env` (optional, for local seeding):
  - [x] `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`
  - [x] `FIREBASE_DATABASE_ID=sms-db`
  - [x] `SETUP_SECRET`, `DEFAULT_SEED_PASSWORD`
- [x] **Render** (`aviasafe-unified-platform.onrender.com`):
  - [x] `FIREBASE_PROJECT_ID` = `aerosafety-sms-prod`
  - [x] `FIREBASE_CLIENT_EMAIL` = `firebase-adminsdk-fbsvc@aerosafety-sms-prod.iam.gserviceaccount.com`
  - [x] `FIREBASE_PRIVATE_KEY` = new private key (JSON-escaped `\n`)
  - [x] `FIREBASE_DATABASE_ID` = `sms-db` (already set)
  - [x] `SETUP_SECRET` = (set)
  - [x] `DEFAULT_SEED_PASSWORD` = (set)
  - [x] `DISABLE_DESTRUCTIVE_ENDPOINTS` = `true` (seeding already done; keep destructive endpoints off)
  - [x] `ALLOWED_ORIGINS` = `https://sms.aviasafesystems.com,https://aerosafety-sms-prod.web.app,http://localhost:3000,http://localhost:8000`

---

## 5. Deploy sequence

- [x] 1. Update repo files (section 3) → commit → push `main` (commit `578a3d8`).
- [x] 2. Deploy hosting: `firebase deploy --only hosting --project aerosafety-sms-prod` (HTTP 200).
- [x] 3. Deploy Firestore rules + indexes to `sms-db`:
      `firebase deploy --only firestore:sms-db --project aerosafety-sms-prod`
      (array-form `firestore` config in `firebase.json` already scoped to `sms-db`).
- [x] 4. Render auto-deploys from push (or trigger manual deploy). Confirm `/health` → `firebase: connected`.
      **Done:** env vars set in Render dashboard + redeployed; `/health` healthy/connected.
- [x] 5. Verify custom domain `sms.aviasafesystems.com` serves the new frontend (HTTP 200, updated `firebase.js`).
      **Done:** DNS CNAME switched; custom domain HTTP 200 + serves `aerosafety-sms-prod` config.

---

## 6. Seed pipeline (after Auth is healthy)

- [x] Mint SUPER_ADMIN token: login verified against new API key
      (`safety.director@caan.gov.np`, seed password).
- [x] Seed executed locally against the new project (`python -m seed.runner`):
      6 tenants, 930 surveys, 620 VSR, 245 MOR, 21 Auth users. `seed_metadata/seed` present.
- [ ] (Not required again — data already in `sms-db`.)
- [x] Verify data landed: `seed_metadata/seed` on `sms-db` confirmed; tenant docs readable.

---

## 7. Post-migration verification

- [x] `/health` → `{"status":"healthy","firebase":"connected"}` (live — verified against new project)
- [x] `/ready` → `{"status":"ready","firebase":"connected"}` (live — verified against new project)
- [x] Seed doc present on `sms-db` (confirmed: `seed_metadata/seed`)
- [x] Tenant docs readable under `tenants/` on `sms-db` (6 tenants)
- [x] Login as `safety.director@caan.gov.np` succeeds (Auth healthy on `aerosafety-sms-prod`)
- [x] Frontend on `aerosafety-sms-prod.web.app` serves updated config (projectId verified in served `firebase.js`)
- [x] Frontend on custom domain loads dashboard (API + Firestore wired to new project; HTTP 200 + new config verified)
- [x] `firebase-admin>=6.6.0` confirmed in local env (named-db `database_id` support)
- [x] CORS: preflight + request from `https://sms.aviasafesystems.com` to Render API accepted (ACAO echo verified)
- [x] Protected API: `/api/v1/admin/risk-matrix` 200 (SUPER_ADMIN); `/api/v1/reports/` 280 tenant reports (AIRLINE_ADMIN)
- [x] CAAN_SMD login + tenant-scoped access verified

---

## 8. Rollback / notes

- Old project `gap-analysis-ssp` (817614332543): keep untouched as archive; do not delete during migration.
- `sms-db` named database name carries over to the new project.
- If any Auth/firestore flakiness recurs on the new project, snapshot logs before contacting support.
- `$300` credit is free infrastructure testing headroom; monitor spend in Billing.
