import requests, time, json

# Wait for Render to build & deploy
time.sleep(180)

base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"
SK = "aviasafe-e2e-setup-2026"

r = requests.post(f"{base}/seed-demo-data", json={"setup_key": SK}, timeout=600)
d = r.json()
print(f"Status: {r.status_code}")
if d.get("success"):
    res = d.get("result", {})
    print(json.dumps(res, indent=2))
else:
    print(json.dumps(d, indent=2)[:2000])
