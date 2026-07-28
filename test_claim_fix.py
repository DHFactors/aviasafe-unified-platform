import requests, json

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

print("=== Buddha Air (new, no claims in token) ===")
resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure"},
    timeout=15,
)
token = resp.json()["idToken"]

r = requests.get(
    "https://aviasafe-unified-platform.onrender.com/api/v1/reports/",
    headers={"Authorization": f"Bearer {token}", "Origin": "https://gap-analysis-ssp.web.app"},
    timeout=15,
)
print(f"Reports: {r.status_code}")
if r.status_code < 400:
    print("  OK")
else:
    print(f"  {r.json()}")

print("\n=== Sita Air (existing, salsafety) ===")
resp2 = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "salsafety@aviasafesystems.com", "password": "Safety123!"},
    timeout=15,
)
data2 = resp2.json()
if "idToken" in data2:
    token2 = data2["idToken"]
    r2 = requests.get(
        "https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/overview?days=90",
        headers={"Authorization": f"Bearer {token2}", "Origin": "https://gap-analysis-ssp.web.app"},
        timeout=15,
    )
    print(f"Dashboard: {r2.status_code}")
    if r2.status_code == 200:
        d = r2.json()
        dd = d.get("data", {})
        print(f"  totalReports: {dd.get('totalReports')}")
        print(f"  openHazards: {dd.get('openHazards')}")
    else:
        print(f"  {r2.json()}")
else:
    print(f"Login error: {data2}")
