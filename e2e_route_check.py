import requests

spec = requests.get('https://aviasafe-unified-platform.onrender.com/openapi.json', timeout=15).json()
paths = spec['paths']

# Reporting endpoints
print('=== Reporting Endpoints ===')
for p in sorted(paths.keys()):
    if 'reporting' in p:
        for method, details in paths[p].items():
            params = details.get('parameters', [])
            body = details.get('requestBody', {})
            print(f'{method.upper()} {p}')
            for param in params:
                loc = param.get('in', '?')
                name = param.get('name', '?')
                required = param.get('required', False)
                print(f'  param: {name} (in: {loc}, required: {required})')
            if body:
                schema = body.get('content',{}).get('application/json',{}).get('schema',{})
                ref = schema.get('$ref', 'inline')
                print(f'  body schema: {ref}')
                if ref == 'inline':
                    props = list(schema.get('properties',{}).keys())
                    print(f'  body props: {props[:4]}')
            print()

# VSR endpoint
print('=== VSR/MOR Endpoints ===')
for p in sorted(paths.keys()):
    if '/vsr' in p or '/mor' in p:
        for method, details in paths[p].items():
            print(f'{method.upper()} {p}')
            body = details.get('requestBody', {})
            schema = body.get('content',{}).get('application/json',{}).get('schema',{})
            ref = schema.get('$ref', '')
            print(f'  schema ref: {ref}')
            if ref:
                # Extract schema name from ref
                name = ref.split('/')[-1]
                s = spec.get('components',{}).get('schemas',{}).get(name, {})
                req = s.get('required', [])
                print(f'  required: {req[:6]}')
                props = list(s.get('properties',{}).keys())
                print(f'  fields: {props[:6]}...')
            print()

# Verification routes
print('=== Verification Routes ===')
for p in sorted(paths.keys()):
    if 'verification' in p:
        for method, details in paths[p].items():
            print(f'{method.upper()} {p}')

# Diversion routes
print('\n=== Diversion Routes ===')
for p in sorted(paths.keys()):
    if 'diversion' in p:
        for method, details in paths[p].items():
            print(f'{method.upper()} {p}')
