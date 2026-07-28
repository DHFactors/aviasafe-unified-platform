import requests, json, base64, time

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

# Re-set claims for Buddha Air (will also revoke tokens now)
r = requests.post(
    "https://aviasafe-unified-platform.onrender.com/api/v1/admin/setup-claims",
    json={
        "setup_key": "aviasafe-e2e-setup-2026",
        "users": [{"email": "buddhaair@buddhaair.com", "role": "AIRLINE_ADMIN", "tenant_id": "buddha-air"}]
    },
)
print(f"setup-claims: {r.status_code} {json.dumps(r.json(), indent=2)}")

# Wait a moment for Firebase propagation
time.sleep(2)

# Sign in fresh - should now include claims
resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure"},
)
data = resp.json()
token = data["idToken"]
parts = token.split(".")
pad = 4 - len(parts[1]) % 4
if pad == 4:
    pad = 0
payload = json.loads(base64.b64decode(parts[1] + "=" * pad))
print(f"Token claims: role={payload.get('role')}, tenant_id={payload.get('tenant_id')}")
print(f"All keys: {list(payload.keys())}")
