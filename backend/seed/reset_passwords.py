#!/usr/bin/env python3
"""
Reset per-user passwords for beta testing and write a credential CSV.

Generates a unique random password for every seeded Auth user, updates
Firebase Auth, and writes:

    <project_root>/beta-testing-credentials.csv

Columns: tenant,role,email,full_name,password

WARNING: this OVERWRITES the shared DEFAULT_SEED_PASSWORD for every user.
Any user not in the generated list is left untouched.
"""

import sys
import csv
import secrets
import string
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level:<7} | {message}", level="INFO")

ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT / "beta-testing-credentials.csv"

CHARSET = string.ascii_letters + string.digits
PASSWORD_LENGTH = 16


def random_password() -> str:
    return "".join(secrets.choice(CHARSET) for _ in range(PASSWORD_LENGTH))


def build_user_specs():
    from seed.config import DEMO_USERS, OPERATOR_PROFILES

    specs = []

    for u in DEMO_USERS:
        specs.append(
            {
                "uid": u["uid"],
                "email": u["email"],
                "full_name": u["full_name"],
                "role": u["role"],
                "tenant": "CAAN",
            }
        )

    for profile in OPERATOR_PROFILES:
        op_id = profile["id"]
        domain = profile["email_domain"]
        tenant_name = profile["name"]
        specs.extend(
            [
                {
                    "uid": f"sm-{op_id}-001",
                    "email": f"safety.{op_id}@{domain}",
                    "role": "AIRLINE_ADMIN",
                    "tenant": tenant_name,
                },
                {
                    "uid": f"ae-{op_id}-001",
                    "email": f"ae.{op_id}@{domain}",
                    "role": "AIRLINE_ADMIN",
                    "tenant": tenant_name,
                },
                {
                    "uid": f"mgr-{op_id}-001",
                    "email": f"manager.{op_id}@{domain}",
                    "role": "USER",
                    "tenant": tenant_name,
                },
            ]
        )

    return specs


def main():
    from app.core.config import settings
    from app.firebase import initialize_firebase, get_auth

    initialize_firebase()
    auth = get_auth()

    specs = build_user_specs()
    logger.info(f"Generated {len(specs)} unique passwords")

    rows = []
    for spec in specs:
        pwd = random_password()
        try:
            auth.update_user(spec["uid"], password=pwd)
            rows.append(
                {
                    "tenant": spec["tenant"],
                    "role": spec["role"],
                    "email": spec["email"],
                    "full_name": spec.get("full_name", ""),
                    "password": pwd,
                }
            )
            logger.info(f"Updated {spec['email']} ({spec['role']} / {spec['tenant']})")
        except Exception as e:
            logger.error(f"FAILED {spec['email']} ({spec['uid']}): {e}")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tenant", "role", "email", "full_name", "password"],
        )
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} credentials to {OUT_CSV}")
    logger.info("NOTE: OLD shared seed password no longer works for these users.")


if __name__ == "__main__":
    main()
