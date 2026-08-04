# Migration Checklist — New Firebase/GCP Project

> **Purpose:** Migrate the AviaSAFE SMS Platform off the broken `gap-analysis-ssp`
> project (Auth stuck in `PROJECT_SOFT_DELETED` after project undelete) onto a
> fresh Google Cloud project with a new $300 credit billing account.
>
> **Status:** `IN PROGRESS` (blocked on operator creating the new project)
>
> **Date started:** 2026-08-04

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

- [ ] **A. Create GCP project**
  - Log into Google Cloud Console with the $300-credit account.
  - Click project dropdown → **New Project**.
  - Suggested name/ID: `aerosafety-sms-prod` (or chosen ID).
- [ ] **B. Link to Firebase**
  - Open [Firebase Console](https://console.firebase.google.com).
  - **Add project** → *Import Google project* → select the project from step A.
  - This binds the $300 billing profile automatically.
- [ ] **C. Enable services**
  - **Authentication** → Sign-in method → enable **Email/Password**.
  - **Firestore Database** → create database named **`sms-db`** (choose a region, e.g. `us-west1` like before, or `nam5`).
  - (Optional) **App Check**, **Storage** — only if needed.
- [ ] **D. Create Firebase web app** (for the frontend)
  - Project Settings → Your apps → Add web app (`</>`).
  - Copy the web SDK config: `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`.
- [ ] **E. Generate service account key**
  - Project Settings → Service accounts → **Generate new private key**.
  - Save the JSON securely. Used for `FIREBASE_PRIVATE_KEY` + `FIREBASE_CLIENT_EMAIL` on Render / local `.env`.
- [ ] **F. Re-link custom domain**
  - Firebase Hosting → **Add custom domain** → `sms.aviasafesystems.com`.
  - Update DNS as prompted (will re-provision SSL).
  - Note: `gap-analysis-ssp.web.app` will no longer serve; the new default is `<new-id>.web.app`.

---

## 3. Files to update (repo) — I can do this once you paste the new config

New values needed:
- [ ] New **project ID** (from step A / D)
- [ ] New **web app config** (from step D)
- [ ] New **service account** email + private key (from step E)

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

- [ ] **Render** (`aviasafe-unified-platform.onrender.com`):
  - [ ] `FIREBASE_PROJECT_ID` = `<new-id>`
  - [ ] `FIREBASE_CLIENT_EMAIL` = new service account email
  - [ ] `FIREBASE_PRIVATE_KEY` = new private key (JSON-escaped `\n`)
  - [ ] `FIREBASE_DATABASE_ID` = `sms-db`
  - [ ] `SETUP_SECRET` = (already set)
  - [ ] `DEFAULT_SEED_PASSWORD` = (already set)
  - [ ] `DISABLE_DESTRUCTIVE_ENDPOINTS` = `false` (needed for `/seed-demo-data`)
  - [ ] `ALLOWED_ORIGINS` = `https://sms.aviasafesystems.com,https://<new-id>.web.app,...`
- [ ] **Local** `backend/.env` (optional, for local seeding):
  - [ ] `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`
  - [ ] `FIREBASE_DATABASE_ID=sms-db`
  - [ ] `SETUP_SECRET`, `DEFAULT_SEED_PASSWORD`

---

## 5. Deploy sequence

- [ ] 1. Update repo files (section 3) → commit → push `main`.
- [ ] 2. Deploy hosting: `firebase deploy --only hosting --project <new-id>`.
- [ ] 3. Deploy Firestore rules + indexes to `sms-db`:
      `firebase deploy --only firestore:<new-database-id> --project <new-id>`
      (array-form `firestore` config in `firebase.json` already scoped to `sms-db`).
- [ ] 4. Render auto-deploys from push (or trigger manual deploy). Confirm `/health` → `firebase: connected`.
- [ ] 5. Verify custom domain `sms.aviasafesystems.com` serves the new frontend (HTTP 200, updated `firebase.js`).

---

## 6. Seed pipeline (after Auth is healthy)

- [ ] Mint SUPER_ADMIN token:
      `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<new-apiKey>`
      body: `{"email":"safety.director@caan.gov.np","password":"<DEFAULT_SEED_PASSWORD>","returnSecureToken":true}`
      → returns `idToken`.
- [ ] Call seed endpoint:
      `POST https://aviasafe-unified-platform.onrender.com/api/v1/admin/seed-demo-data`
      headers: `Authorization: Bearer <idToken>`
      body: `{"setup_key":"<SETUP_SECRET>"}`
      → expect `{"success":true,"result":{surveys:930, vsr_reports:620, mor_reports:245, tenants:20, users:...}}`
- [ ] Alternative: `python scripts/seed/run_seed.py` with `SUPER_ADMIN_ID_TOKEN` + `SETUP_SECRET` env vars.
- [ ] Verify data landed: `GET https://firestore.googleapis.com/v1/projects/<new-id>/databases/sms-db/documents/seed_metadata/seed`.

---

## 7. Post-migration verification

- [ ] `/health` → `{"status":"healthy","firebase":"connected"}`
- [ ] `/ready` → `{"status":"ready","firebase":"connected"}`
- [ ] Seed doc present on `sms-db` (section 6 last step)
- [ ] Tenant docs readable under `tenants/` on `sms-db`
- [ ] Login as `safety.director@caan.gov.np` succeeds (Auth no longer `PROJECT_SOFT_DELETED`)
- [ ] Frontend on custom domain loads dashboard (API + Firestore wired to new project)
- [ ] `firebase-admin>=6.6.0` confirmed in Docker build (named-db `database_id` support)
- [ ] CORS: request from `https://sms.aviasafesystems.com` to Render API accepted

---

## 8. Rollback / notes

- Old project `gap-analysis-ssp` (817614332543): keep untouched as archive; do not delete during migration.
- `sms-db` named database name carries over to the new project.
- If any Auth/firestore flakiness recurs on the new project, snapshot logs before contacting support.
- `$300` credit is free infrastructure testing headroom; monitor spend in Billing.
