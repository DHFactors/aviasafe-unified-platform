# AviaSAFE SMS — Closed Beta Demo Accounts

Versioned reference for beta testers. Verified **2026-08-06**.

## Access

| Item | Value |
|------|-------|
| **Beta URL** | https://sms-beta.web.app |
| **Shared demo password** | `{SHARED_DEMO_PASSWORD}` — issued by the AviaSAFE administrator; do not share or publish |
| **Support** | info@aviasafesystems.com |

> The beta runs on an isolated database (`sms-db-beta`) with demo data only. Nothing entered here touches production.

## Operator Accounts (AIRLINE_ADMIN / USER)

Each participating airline has three demo accounts. Assign one airline per tester (or one per role where needed).

| Airline | Safety Manager (Admin) | Airline Executive (Admin) | Manager (User) |
|---------|------------------------|---------------------------|----------------|
| Buddha Air | safety.buddha-air@buddhaair.com | ae.buddha-air@buddhaair.com | manager.buddha-air@buddhaair.com |
| Yeti Airlines | safety.yeti-airlines@yetiairlines.com | ae.yeti-airlines@yetiairlines.com | manager.yeti-airlines@yetiairlines.com |
| Summit Air | safety.summit-air@summitair.com.np | ae.summit-air@summitair.com.np | manager.summit-air@summitair.com.np |
| Sita Air | safety.sita-air@sitaair.com.np | ae.sita-air@sitaair.com.np | manager.sita-air@sitaair.com.np |
| Air Dynasty Heli Services | safety.air-dynasty@airdynasty.com.np | ae.air-dynasty@airdynasty.com.np | manager.air-dynasty@airdynasty.com.np |
| Simrik Air | safety.simrik-air@simrikair.com | ae.simrik-air@simrikair.com | manager.simrik-air@simrikair.com |
| Tara Air | safety.tara-air@taraair.com | ae.tara-air@taraair.com | manager.tara-air@taraair.com |

All operator accounts are bound to their airline tenant (role `AIRLINE_ADMIN` for Safety Manager/Executive, `USER` for Manager).

## CAAN / Regulatory Accounts

| Account | Email | Role |
|---------|-------|------|
| Super Admin | safety.director@caan.gov.np | `SUPER_ADMIN` |
| CAAN SMS Director | director.safety@caan.gov.np | `CAAN_SMD` |
| CAAN SMS Inspector | sms.inspector@caan.gov.np | `CAAN_SMD` |

## What Testers Should Do

1. Log in at https://sms-beta.web.app with the assigned account.
2. Follow the checklist (`docs/BETA_TEST_CHECKLIST.md`) — VSR, hazard registration, risk-matrix, CAPs, rate-limit behavior.
3. Report issues via the feedback form (see invitation email).
4. Use the beta for **testing only** — do not enter real personal data.

## Admin Notes (remove before sharing)

- All 24 demo accounts use the same password = value of `DEFAULT_SEED_PASSWORD` in `backend/.env`. Fill `{SHARED_DEMO_PASSWORD}` above before distributing this document.
- Accounts were reset to that password on **2026-08-06** after a cleanup pass; re-run the reset if credentials drift.
- If a tester must use Google sign-in, their Google email must be added as `safety_manager.email` on the corresponding tenant doc in `sms-db-beta` (fallback resolution in `backend/app/middleware/auth.py`).
