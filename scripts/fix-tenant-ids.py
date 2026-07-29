"""
Fix tenant_id mismatch between provisioned users (hyphen) and seed data (underscore).
"""

import firebase_admin
from firebase_admin import auth, credentials
import os

cred_path = os.path.join(os.path.dirname(__file__), "..", "service-account.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

FIXES = {
    "buddhaair@buddhaair.com": "buddha_air",
    "info@sitaair.com": "sita_air",
    "info@summitair.com.np": "summit_air",
    "info@yetiairlines.com": "yeti_airlines",
    "info@airdynasty.com": "air_dynasty",
    "info@simrikair.com": "simrik_air",
}

for email, correct_tid in FIXES.items():
    try:
        user = auth.get_user_by_email(email)
        existing = user.custom_claims or {}
        existing["tenant_id"] = correct_tid
        auth.update_user(user.uid, custom_claims=existing)
        print(f"  ✅ {email}: tenant_id → {correct_tid}")
    except Exception as e:
        print(f"  ❌ {email}: {e}")

print("\nDone. These 6 users can now see their seed data on the dashboard.")
