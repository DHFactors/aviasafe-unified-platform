import requests
import time

base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"

print("Waiting for Render deploy...")
time.sleep(30)

print("Calling fix-tenant-ids...")
r = requests.post(f"{base}/fix-tenant-ids", json={"setup_key": "aviasafe-e2e-setup-2026"}, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    for r2 in r.json().get("results", []):
        s = r2.get("status", "?")
        tid = r2.get("tenant_id", "")
        print(f"  {r2['email']}: {s}  tenant_id={tid}")
else:
    print(r.text[:500])
