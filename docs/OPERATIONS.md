# Operations Manual

Day-to-day operations, administration, monitoring, and recovery for the AviaSAFE platform.

## 1. Roles & Who Does What

| Role | Typical operator | Operations responsibilities |
|---|---|---|
| `SUPER_ADMIN` | CAAN top-level director / platform owner | Provision airlines, fix tenant ids, risk-matrix defaults, seed demo data, claim setup |
| `CAAN_SMD` | Regulator / SSP inspectorate | Cross-tenant read, confirm risk assessments on behalf of the State |
| `AIRLINE_ADMIN` | Airline safety manager | Manage own-tenant reports, hazards, CAN/CAP, risk-matrix config, users |
| `USER` | Airline reporter | Submit VSR/MOR, view own-tenant data |

## 2. User Management

### 2.1 Registration

- Public registration creates an account with role `AIRLINE_ADMIN` (the tenant is derived from the
  registrant's email domain).
- Claim propagation can lag by a few seconds; the API falls back to an email→tenant lookup in that
  window (see [SECURITY.md](./SECURITY.md)).

### 2.2 Provisioning airlines (SUPER_ADMIN)

`POST /api/v1/admin/provision-airlines` — requires a SUPER_ADMIN ID token **and** `SETUP_SECRET`:

```bash
curl -X POST https://<host>/api/v1/admin/provision-airlines \
  -H "Authorization: Bearer <SUPER_ADMIN_ID_TOKEN>" \
  -H "X-Setup-Key: <SETUP_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"password": "<DEFAULT_PROVISION_PASSWORD>"}'
```

Creates the tenant(s), admin users, and CAAN cross-tenant accounts. If `SETUP_SECRET` is unset, the
endpoint returns `503` (fail-closed).

### 2.3 Fix tenant IDs

`POST /api/v1/admin/fix-tenant-ids` — reconciles `_` vs `-` tenant-id normalization drift
(SUPER_ADMIN only).

### 2.4 Other admin endpoints

See [API.md](./API.md) — `admin` router. Data-destructive endpoints
(`/seed-demo-data`, `/create-seed-users`) return `404` when `DISABLE_DESTRUCTIVE_ENDPOINTS=true`
(default), as set in production.

## 3. Monitoring & Health

| Endpoint | Purpose |
|---|---|
| `/health` | Basic liveness (process up) |
| `/live` | Liveness probe (used by Render / Cloud Run) |
| `/ready` | Readiness probe (dependency checks) |
| `/metrics` | Prometheus-style counters (AI results, request counts) |

Request logging middleware emits per-request records (UUID, method, path, status, duration, user).
Backend logs use **loguru** and are written to `backend/logs/`.

## 4. Rate Limiting

- Default: **60 requests/minute per IP** (in-memory).
- When `REDIS_URL` is set, limits are Redis-backed and can be per-tenant on sensitive endpoints.
- On rate-limit breach clients receive `429`; raised thresholds and per-tenant policies are a
  tuning decision for the operator.

## 5. Backup & Disaster Recovery

**Current state (honest):**
- **No automated Firestore backups or PITR** are configured. Firestore by default retains a
  snapshot only via Google Cloud Backup/PITR settings, which must be enabled by an operator.
- **Recommended action (outstanding):** enable Firestore Backups (or PITR at minimum) for
  `gap-analysis-ssp`; see [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md).

**Recovery steps if data is lost:**
1. Restore the most recent Firestore backup to the same project (or re-seed from
   `backend/seed` for the demo dataset).
2. Verify Auth user records still resolve (Auth is separate from Firestore; recreate users via
   `provision-airlines`/`create-seed-users` as needed).
3. Confirm security rules and indexes are the deployed versions.

## 6. TLS / CORS / Domains

- All client traffic is HTTPS (Firebase Hosting + Render managed TLS).
- CORS allow-list is `ALLOWED_ORIGINS` (default includes the Hosting origin and local dev ports).
- If you add a custom domain, add it to `ALLOWED_ORIGINS` and the Hosting custom-domain setup.

## 7. Common Operations Playbook

| Situation | Action |
|---|---|
| Backend unhealthy | Check `backend/logs/`, `/health`; verify Firestore creds; Render logs; rollback deploy (§DEPLOYMENT). |
| User can't sign in | Verify Auth user exists; re-send email/password reset; check custom claims propagation. |
| Cross-tenant data appears | Check `tenant_id` normalization (`/fix-tenant-ids`); verify token claims; audit rules. |
| Rate-limit spam | Adjust `RATE_LIMIT_PER_MINUTE` or enable Redis-backed policy. |
| App Check rejections | Verify web app key (reCAPTCHA v3) in Firebase console matches `public/js/firebase.js`. |
| Demo data needed | `python -m seed.runner --force` (backend) — destructive, staging only. |
| Incident / security event | Document in status report; rotate affected secrets; review Firestore rules. |

## 8. Change Management

- All functional/architectural changes require approval (Product Charter governance rule).
- Every change must keep `python -m pytest tests/ -q` green.
- Record changes + current commit in `PROJECT_STATUS_REPORT_02AUG2026.md`.
