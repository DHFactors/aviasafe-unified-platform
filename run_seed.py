import requests, time

print("Waiting for Render deploy...")
time.sleep(90)

base = "https://aviasafe-unified-platform.onrender.com/api/v1/admin"
r = requests.post(f"{base}/seed-demo-data", json={"setup_key": "aviasafe-e2e-setup-2026"}, timeout=300)
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
    print(f"  Error: {d.get('error', 'unknown')}")
