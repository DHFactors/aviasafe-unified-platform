import requests

api_key = "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc"

r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
    json={"email": "buddhaair@buddhaair.com", "password": "AviaSAFE2026!Secure", "returnSecureToken": True}, timeout=15)
t = r.json()["idToken"]
h = {"Authorization": f"Bearer {t}", "Origin": "https://gap-analysis-ssp.web.app"}

base = "https://aviasafe-unified-platform.onrender.com/api/v1/dashboard"
eps = [
    "/overview?days=90",
    "/risk?days=90",
    "/trends?days=180",
    "/hazards?days=90",
    "/recent?days=90&page=1&page_size=10",
]
for ep in eps:
    r = requests.get(f"{base}{ep}", headers=h, timeout=30)
    d = r.json()
    data = d.get("data")
    dt = type(data).__name__
    if isinstance(data, dict):
        ks = list(data.keys())[:4]
        preview = f"dict({ks})"
        if "kpis" in data:
            k = data["kpis"]
            preview += f" total={k.get('total_reports',0)}"
        elif "items" in data:
            preview += f" items={len(data.get('items',[]))}"
    elif isinstance(data, list):
        preview = f"list[{len(data)}]"
    else:
        preview = str(data)[:60]
    print(f"  {ep}: {r.status_code} {dt} {preview}")
