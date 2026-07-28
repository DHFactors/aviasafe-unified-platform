import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

# Test with Buddha Air (newly provisioned, confirmed claims work)
email = "buddhaair@buddhaair.com"
pw = "AviaSAFE2026!Secure"

resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": email, "password": pw},
)
data = resp.json()
if "error" in data:
    print(f"Buddha Air login error: {data['error']['message']}")
else:
    token = data["idToken"]
    parts = token.split(".")
    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.b64decode(payload_b64))
    print(f"Buddha Air claims: role={payload.get('role')}, tenant_id={payload.get('tenant_id')}")

r = requests.get(
    "https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/overview?days=90",
    headers={
        "Authorization": f"Bearer {token}",
        "Origin": "https://gap-analysis-ssp.web.app"
    },
)
print(f"Status: {r.status_code}")
print(f"CORS header: {r.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
print(f"Content-Type: {r.headers.get('Content-Type', 'NOT SET')}")
if r.status_code == 200:
    d = r.json()
    print(f"success: {d.get('success')}")
    dd = d.get("data")
    if dd:
        print(f"totalReports: {dd.get('totalReports')}")
        print(f"openHazards: {dd.get('openHazards')}")
    else:
        print(f"Response: {json.dumps(d, indent=2)[:500]}")
else:
    print(f"Response: {json.dumps(r.json(), indent=2)[:500]}")
