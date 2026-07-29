import requests, json

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"
r = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure", "returnSecureToken": True},
    timeout=15,
)
token = r.json()["idToken"]
h = {"Authorization": f"Bearer {token}", "Origin": "https://gap-analysis-ssp.web.app"}

paths = [
    "/api/v1/verification/verifications/stats",
    "/api/v1/verification/stats",
    "/api/verification/verifications/stats",
    "/api/verification/stats",
]
for p in paths:
    r = requests.get(f"https://aviasafe-unified-platform.onrender.com{p}", headers=h, timeout=15)
    err = r.json().get("error", "OK")
    print(f"{p}: {r.status_code} - {err[:100]}")
