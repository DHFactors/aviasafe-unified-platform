// List Firestore databases in a project using the backend/.env service account.
// Usage: node scripts/firebase/list-databases.js [projectId...]
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function loadEnv() {
    const raw = fs.readFileSync(path.join(__dirname, '..', '..', 'backend', '.env'), 'utf8');
    const env = {};
    for (const line of raw.split(/\r?\n/)) {
        const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)$/);
        if (m && !line.trim().startsWith('#')) {
            let v = m[2];
            if (v.length >= 2 && v[0] === '"' && v[v.length - 1] === '"') v = v.slice(1, -1);
            env[m[1]] = v;
        }
    }
    return env;
}

function getAccessToken(env, scope) {
    return new Promise((resolve, reject) => {
        const iat = Math.floor(Date.now() / 1000);
        const exp = iat + 3600;
        const header = { alg: 'RS256', typ: 'JWT' };
        const payload = {
            iss: env.FIREBASE_CLIENT_EMAIL,
            scope: scope,
            aud: env.FIREBASE_TOKEN_URI || 'https://oauth2.googleapis.com/token',
            iat,
            exp,
        };
        const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
        const data = b64(header) + '.' + b64(payload);
        const sig = crypto.sign('RSA-SHA256', Buffer.from(data), {
            key: (env.FIREBASE_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
        });
        const assertion = data + '.' + sig.toString('base64url');
        const body = new URLSearchParams({
            grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            assertion,
        });
        fetch(env.FIREBASE_TOKEN_URI || 'https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body,
        }).then((r) => r.json()).then((j) => {
            if (!j.access_token) return reject(new Error('Token exchange failed: ' + JSON.stringify(j)));
            resolve(j.access_token);
        }).catch(reject);
    });
}

async function listDatabases(token, projectId) {
    const url = `https://firestore.googleapis.com/v1/projects/${projectId}/databases`;
    const r = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
        console.log(`${projectId}: HTTP ${r.status} ${JSON.stringify(j.error || {}).slice(0, 300)}`);
        return;
    }
    const names = (j.databases || []).map((d) => d.name.split('/databases/')[1] + '  [' + (d.type || '?') + ']');
    console.log(`${projectId}: ${names.length ? names.join(', ') : '(no databases listed)'}`);
}

async function main() {
    const env = loadEnv();
    const projects = process.argv.slice(2);
    if (!projects.length) projects.push(env.FIREBASE_PROJECT_ID);
    const scope = 'https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/datastore';
    const token = await getAccessToken(env, scope);
    for (const p of projects) await listDatabases(token, p);
}

main().catch((e) => { console.error(e); process.exit(1); });
