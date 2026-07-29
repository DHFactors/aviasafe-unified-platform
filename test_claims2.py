import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure", "returnSecureToken": True}, timeout=15)
token = r.json()["idToken"]

parts = token.split(".")
padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
payload = json.loads(base64.b64decode(padded))
print("All keys:", list(payload.keys()))
for k, v in payload.items():
    print(f"  {k}: {v}")
