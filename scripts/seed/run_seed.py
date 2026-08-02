import os
import requests
import time

# /seed-demo-data is gated behind a SUPER_ADMIN ID token (Authorization header)
# plus the server-side setup key. Requires DISABLE_DESTRUCTIVE_ENDPOINTS=False
# on the deployed environment. All secrets come from the environment.
TOKEN = os.environ.get("SUPER_ADMIN_ID_TOKEN")
SETUP_KEY = os.environ.get("SETUP_SECRET")

if not TOKEN or not SETUP_KEY:
    raise SystemExit("SUPER_ADMIN_ID_TOKEN and SETUP_SECRET env vars are required")

time.sleep(30)
base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"
headers = {"Authorization": f"Bearer {TOKEN}"}
r = requests.post(
    f"{base}/seed-demo-data",
    json={"setup_key": SETUP_KEY},
    headers=headers,
    timeout=600,
)
print(f"Status: {r.status_code}")
d = r.json()
if r.status_code == 200:
    result = d.get("result", {})
    print(f"  Surveys: {result.get('surveys', 0)}")
    print(f"  VSR:     {result.get('vsr_reports', 0)}")
    print(f"  MOR:     {result.get('mor_reports', 0)}")
    print(f"  Tenants: {result.get('tenants', 0)}")
    print(f"  Users:   {result.get('users', 0)}")
else:
    print(f"  Error: {d.get('error', str(d)[:500])}")
