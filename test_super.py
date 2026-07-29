import requests, json

API_KEY = 'AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc'

# Login as super admin
login_url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}'
r = requests.post(login_url, json={
    'email': 'safety.director@caan.gov.np',
    'password': 'Demo@123456',
    'returnSecureToken': True
}, timeout=30)

if not r.ok:
    print('Login failed:', r.text[:500])
    exit(1)

id_token = r.json()['idToken']
print('Logged in as SUPER_ADMIN')

headers = {'Authorization': f'Bearer {id_token}'}

# Try CAAN overview
r2 = requests.get('https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/overview',
    headers=headers, timeout=30)
print('CAAN overview:', json.dumps(r2.json(), indent=2)[:1000])

# Try tenants list
r3 = requests.get('https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/reports',
    headers=headers, timeout=30)
print('Reports:', json.dumps(r3.json(), indent=2)[:500])
