import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

# Sign in with Buddha Air (was tested earlier and worked)
resp = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure"},
    timeout=15,
)
data = resp.json()
token = data["idToken"]

parts = token.split(".")
pad = 4 - len(parts[1]) % 4 or 0
payload = json.loads(base64.b64decode(parts[1] + "=" * pad))
print(f"Buddha Air - role: {payload.get('role')}, tenant: {payload.get('tenant_id')}")

# Now sign in with Salsafety  
resp2 = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "salsafety@aviasafesystems.com", "password": "Safety123!"},
    timeout=15,
)
data2 = resp2.json()
if "idToken" in data2:
    token2 = data2["idToken"]
    parts2 = token2.split(".")
    pad2 = 4 - len(parts2[1]) % 4 or 0
    payload2 = json.loads(base64.b64decode(parts2[1] + "=" * pad2))
    print(f"Salsafety - role: {payload2.get('role')}, tenant: {payload2.get('tenant_id')}")
else:
    print(f"Salsafety login error: {data2}")
