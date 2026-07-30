import requests, json

API_KEY = 'AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc'

login_url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}'
r = requests.post(login_url, json={
    'email': 'safety.buddha-air@buddhaair.com',
    'password': 'Demo@123456',
    'returnSecureToken': True
}, timeout=30)

if not r.ok:
    print('Login failed:', r.text[:500])
    exit(1)

id_token = r.json()['idToken']
print('Logged in OK')

headers = {'Authorization': f'Bearer {id_token}'}
r2 = requests.get('https://aviasafe-unified-platform.onrender.com/api/v1/dashboard/overview?days=90',
    headers=headers, timeout=30)
res = r2.json()
print(json.dumps(res, indent=2)[:2000])
