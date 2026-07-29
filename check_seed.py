import requests, time

time.sleep(30)
base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"
SK = "aviasafe-e2e-setup-2026"

r = requests.post(f"{base}/seed-demo-data", json={"setup_key": SK}, timeout=600)
d = r.json()
print(f"Status: {r.status_code}")
import json
print(json.dumps(d, indent=2)[:2000])
