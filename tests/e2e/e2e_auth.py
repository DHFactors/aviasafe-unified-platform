import requests, json, sys

API_KEY = 'AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc'
FIREBASE_AUTH_URL = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=' + API_KEY
BASE_API = 'https://aviasafe-unified-platform.onrender.com'

users = {
    'airline_admin': {'email': 'sal@aviasafesystems.com', 'password': 'Sal123!'},
    'caan_smd': {'email': 'smd@caanepal.gov.np', 'password': 'Smd123!'},
    'super_admin': {'email': 'admin@aviasafesystems.com', 'password': 'Admin123!'},
    'safety': {'email': 'salsafety@aviasafesystems.com', 'password': 'Safety123!'},
}

tokens = {}
for name, creds in users.items():
    r = requests.post(FIREBASE_AUTH_URL, json={
        'email': creds['email'],
        'password': creds['password'],
        'returnSecureToken': True
    }, timeout=15)
    if r.status_code == 200:
        data = r.json()
        tokens[name] = data['idToken']
        expiry = data.get('expiresIn', '?')
        print(f'{name}: token obtained (expires in {expiry}s)')
    else:
        print(f'{name}: FAILED - {r.status_code} {r.text[:200]}')

if 'airline_admin' in tokens:
    h = {'Authorization': 'Bearer ' + tokens['airline_admin']}
    endpoints = [
        ('GET', '/api/v1/hazards/stats'),
        ('GET', '/api/v1/cans/stats'),
        ('GET', '/api/v1/verification/verifications/stats'),
        ('GET', '/api/v1/flight-diversions/stats'),
        ('GET', '/api/v1/reporting/quarterly'),
        ('GET', '/api/v1/dashboard/overview'),
        ('GET', '/api/v1/reports/'),
    ]
    print('\n--- Testing with airline_admin ---')
    for method, path in endpoints:
        fn = getattr(requests, method.lower())
        r = fn(BASE_API + path, headers=h, timeout=15)
        ok = r.status_code in [200, 201, 404]
        status = 'OK' if ok else 'FAIL(' + str(r.status_code) + ')'
        print('  ' + method + ' ' + path + ': ' + status)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                keys = list(data.keys())[:6]
                print('    keys: ' + str(keys))
            elif isinstance(data, list):
                print('    count: ' + str(len(data)))

# Save tokens for later use
with open('e2e_tokens.json', 'w') as f:
    json.dump(tokens, f)
print('\nTokens saved to e2e_tokens.json')
