# Airline Onboarding Reference (20 Airlines)

> **Credential policy (RC-3):** passwords are **never documented in plaintext**. Onboarding accounts
> are provisioned with the password configured in the backend environment
> (`DEFAULT_PROVISION_PASSWORD` for `/provision-airlines`, `DEFAULT_SEED_PASSWORD` for the seed
> pipeline). Distribute credentials to each airline through a secure channel (email/password reset),
> not via this document.

## Tenant Index

| # | Airline | Tenant ID | Login email |
|---|---|---|---|
| 1 | Buddha Air | `buddha-air` | `buddhaair@buddhaair.com` |
| 2 | Nepal Airlines | `nepal-airlines` | `info@nac.com.np` |
| 3 | Shree Airlines | `shree-airlines` | `info@shreeairlines.com` |
| 4 | Sita Air | `sita-air` | `info@sitaair.com` |
| 5 | Summit Air | `summit-air` | `info@summitair.com.np` |
| 6 | Tara Air | `tara-air` | `info@taraair.com` |
| 7 | Yeti Airlines | `yeti-airlines` | `info@yetiairlines.com` |
| 8 | Makalu Air | `makalu-air` | `info@makaluair.com` |
| 9 | Himalaya Airlines | `himalaya-airlines` | `info@himalaya-airlines.com` |
| 10 | Air Dynasty Heli Services | `air-dynasty` | `info@airdynasty.com` |
| 11 | Altitude Air | `altitude-air` | `info@altitudeair.com.np` |
| 12 | Annapurna Helicopter | `annapurna-heli` | `info@annapurnaheli.com` |
| 13 | Fishtail Air | `fishtail-air` | `info@fishtailair.com` |
| 14 | Heli Everest | `heli-everest` | `info@helieverest.com` |
| 15 | Kailash Helicopter Services | `kailash-helicopter` | `info@kailashhelicopter.com` |
| 16 | Manang Air | `manang-air` | `info@manangair.com` |
| 17 | Mountain Helicopters | `mountain-helicopters` | `info@mountainhelicopters.com` |
| 18 | Mustang Helicopter | `mustang-helicopter` | `info@mustanghelicopter.com` |
| 19 | Prabhu Helicopters | `prabhu-helicopters` | `info@prabhuhelicopters.com` |
| 20 | Simrik Air | `simrik-air` | `info@simrikair.com` |

## Per-Tenant Links

For any tenant `T` (e.g. `buddha-air`), the portal pages are:

| Page | URL |
|---|---|
| Safety Dashboard | `https://sms.aviasafesystems.com/safety.html?tenant=T` |
| Survey | `https://sms.aviasafesystems.com/survey/?tenant=T` |
| VSR Form | `https://sms.aviasafesystems.com/report/vsr.html?tenant=T` |
| MOR Form | `https://sms.aviasafesystems.com/report/mor.html?tenant=T` |

## Quick Reference

| Link | URL |
|---|---|
| Platform Root | https://sms.aviasafesystems.com |
| CAAN Dashboard | https://sms.aviasafesystems.com/caan.html |
| Admin Portal | https://sms.aviasafesystems.com/admin/ |

## Provisioning

Tenants are created via `POST /api/v1/admin/provision-airlines` (SUPER_ADMIN token + `SETUP_SECRET`).
See [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) and [API.md](./API.md). The demo seed dataset (6 profiles) is
loaded with `python -m seed.runner` — see [DEMO_GUIDE.md](../docs/archive/DEMO_GUIDE.md).
