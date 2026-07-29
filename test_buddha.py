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
        if "kpis" in data:
            k = data["kpis"]
            print(f"  {ep}: 200 KPIs total={k.get('total_reports',0)} open={k.get('open_reports',0)}")
        elif "items" in data:
            print(f"  {ep}: 200 items={len(data.get('items',[]))} total={data.get('total',0)}")
        else:
            print(f"  {ep}: 200 {dict((k,type(v).__name__) for k,v in list(data.items())[:4])}")
    elif isinstance(data, list):
        print(f"  {ep}: 200 list[{len(data)}] first={data[0] if data else 'empty'}")
    else:
        print(f"  {ep}: {r.status_code} {dt}")
