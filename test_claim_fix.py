import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

# Use returnSecureToken=true as the browser SDK does
resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure", "returnSecureToken": True},
    timeout=15,
)
token = resp.json()["idToken"]

parts = token.split(".")
pad = 4 - len(parts[1]) % 4 or 0
payload = json.loads(base64.b64decode(parts[1] + "=" * pad))

print(f"iss in token: {payload.get('iss')}")
print(f"aud in token: {payload.get('aud')}")
print(f"role in token: {payload.get('role')}")
print(f"tenant_id in token: {payload.get('tenant_id')}")

# Now send to debug-verify
r = requests.post(
    "https://aviasafe-unified-platform.onrender.com/api/v1/auth/debug-verify",
    json={"id_token": token},
    timeout=15,
)
res = r.json()
print(f"\nBackend verify: {res.get('success')}")
if res.get("success"):
    decoded = res.get("decoded", {})
    print(f"  role={decoded.get('role')}, tenant={decoded.get('tenant_id')}")
else:
    print(f"  error={res.get('error')[:100]}")
    print(f"  type={res.get('error_type')}")

# Test actual API call
r2 = requests.get(
    "https://aviasafe-unified-platform.onrender.com/api/v1/reports/",
    headers={"Authorization": f"Bearer {token}", "Origin": "https://gap-analysis-ssp.web.app"},
    timeout=15,
)
print(f"\nAPI call /reports/: {r2.status_code}")
print(r2.json() if r2.status_code < 400 else r2.json().get("error"))

# Test dashboard overview (Buddha Air, no data)
r3 = requests.get(
    "https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/overview?days=90",
    headers={"Authorization": f"Bearer {token}", "Origin": "https://gap-analysis-ssp.web.app"},
    timeout=15,
)
print(f"\nAPI call /dashboard/overview: {r3.status_code}")
if r3.status_code == 200:
    d = r3.json().get("data", {})
    print(f"  totalReports={d.get('totalReports')}")
else:
    print(f"  {r3.json().get('error')}")
