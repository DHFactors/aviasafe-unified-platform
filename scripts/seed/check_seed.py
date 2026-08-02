import os
import requests
import time
import json

# See run_seed.py — requires SUPER_ADMIN token + setup key from the environment.
TOKEN = os.environ.get("SUPER_ADMIN_ID_TOKEN")
SK = os.environ.get("SETUP_SECRET")

if not TOKEN or not SK:
    raise SystemExit("SUPER_ADMIN_ID_TOKEN and SETUP_SECRET env vars are required")

# Wait for Render to build & deploy
time.sleep(180)

base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"
headers = {"Authorization": f"Bearer {TOKEN}"}

r = requests.post(f"{base}/seed-demo-data", json={"setup_key": SK}, headers=headers, timeout=600)
d = r.json()
print(f"Status: {r.status_code}")
if d.get("success"):
    res = d.get("result", {})
    print(json.dumps(res, indent=2))
else:
    print(json.dumps(d, indent=2)[:2000])
