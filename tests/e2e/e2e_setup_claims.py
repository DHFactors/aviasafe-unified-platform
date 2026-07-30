import requests

BASE = 'https://aviasafe-unified-platform.onrender.com'

payload = {
    'setup_key': 'aviasafe-e2e-setup-2026',
    'users': [
        {'email': 'admin@aviasafesystems.com', 'role': 'SUPER_ADMIN'},
        {'email': 'sal@aviasafesystems.com', 'role': 'AIRLINE_ADMIN', 'tenant_id': 'sita-air'},
        {'email': 'salsafety@aviasafesystems.com', 'role': 'AIRLINE_ADMIN', 'tenant_id': 'sita-air'},
        {'email': 'smd@caanepal.gov.np', 'role': 'CAAN_SMD'},
    ]
}

r = requests.post(BASE + '/api/v1/admin/setup-claims', json=payload, timeout=30)

print('Status:', r.status_code)
data = r.json()
for result in data.get('results', []):
    email = result['email']
    status = result['status']
    role = result.get('role', '?')
    tenant = result.get('tenant_id', 'none')
    print(f'  {email}: {status} (role={role}, tenant={tenant})')
