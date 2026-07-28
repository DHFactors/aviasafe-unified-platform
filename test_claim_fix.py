import requests, json

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

users = [
    ("sal@aviasafesystems.com", "Sal123!", "airline_admin"),
    ("salsafety@aviasafesystems.com", "Safety123!", "safety"),
    ("smd@caanepal.gov.np", "Smd123!", "caan_smd"),
    ("buddhaair@buddhaair.com", "AviaSAFE2026!Secure", "new_airline"),
]

for email, pw, label in users:
    resp = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
        json={"email": email, "password": pw},
        timeout=15,
    )
    data = resp.json()
    if "idToken" in data:
        token = data["idToken"]
        # Test verify endpoint
        r = requests.post(
            "https://aviasafe-unified-platform.onrender.com/api/v1/auth/verify",
            json={"id_token": token},
            timeout=15,
        )
        print(f"{label} ({email}): verify={r.status_code}")
        if r.status_code == 200:
            print(f"  OK: {json.dumps(r.json(), indent=2)[:200]}")
        else:
            print(f"  FAIL: {r.json().get('error')}")
    else:
        print(f"{label} ({email}): LOGIN FAILED - {data.get('error', {}).get('message', 'unknown')}")
