import requests, json, base64

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

for email, pw in [
    ("buddhaair@buddhaair.com", "AviaSAFE2026!Secure"),
    ("sal@aviasafesystems.com", "Sal123!"),
    ("admin@aviasafesystems.com", "AviaSAFE2026!Secure"),
]:
    resp = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        json={"email": email, "password": pw},
    )
    data = resp.json()
    if "error" in data:
        print(f"{email}: LOGIN FAILED - {data['error']['message']}")
        continue
    token = data["idToken"]
    parts = token.split(".")
    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
    try:
        payload = json.loads(base64.b64decode(payload_b64))
    except Exception as e:
        print(f"{email}: DECODE ERROR - {e}")
        print(f"  payload_b64 (len={len(payload_b64)}): {payload_b64[:50]}...")
        continue
    print(f"{email}: role={payload.get('role')}, tenant_id={payload.get('tenant_id')}")
    print(f"  KEYS: {list(payload.keys())}")

    # Lookup user info to check customAttributes    
    lookup = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
        json={"idToken": token},
    )
    lu = lookup.json()["users"][0]
    print(f"  customAttributes: {lu.get('customAttributes')}")
    print(f"  validSince: {lu.get('validSince')}")
