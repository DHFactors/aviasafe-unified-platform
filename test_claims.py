import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure", "returnSecureToken": True}, timeout=15)
token = r.json()["idToken"]

# Decode JWT payload (second segment)
parts = token.split(".")
padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
try:
    payload = json.loads(base64.b64decode(padded))
    print("Claims:", json.dumps(payload.get("claims", {}), indent=2))
    print("Tenant ID:", payload.get("claims", {}).get("tenant_id", "NOT FOUND"))
except Exception as e:
    print(f"Decode error: {e}")
    print("Payload:", parts[1])
