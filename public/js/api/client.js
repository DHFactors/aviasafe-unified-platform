const ApiClient = {
    _baseUrl: () => (window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || '',

    _waitForFirebase: () => {
        return new Promise(resolve => {
            if (typeof firebase !== 'undefined' && firebase.auth) {
                resolve();
                return;
            }
            const check = setInterval(() => {
                if (typeof firebase !== 'undefined' && firebase.auth) {
                    clearInterval(check);
                    resolve();
                }
            }, 30);
            setTimeout(() => {
                clearInterval(check);
                resolve();
            }, 8000);
        });
    },

    _getToken: async () => {
        await ApiClient._waitForFirebase();
        const user = firebase.auth().currentUser;
        if (!user) {
            window.location.href = '/login.html';
            return null;
        }
        try {
            return await user.getIdToken();
        } catch {
            window.location.href = '/login.html';
            return null;
        }
    },

    _request: async (method, path, body) => {
        const token = await ApiClient._getToken();
        if (!token) return null;

        const url = `${ApiClient._baseUrl()}${path}`;
        const opts = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
        };
        if (body && method !== 'GET') {
            opts.body = JSON.stringify(body);
        }

        let response;
        try {
            response = await fetch(url, opts);
        } catch (err) {
            throw new Error(`Network error: ${err.message}`);
        }

        if (response.status === 401) {
            window.location.href = '/login.html';
            return null;
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
            throw new Error(err.detail || `Request failed: ${response.status}`);
        }

        const json = await response.json();
        return json.data !== undefined ? json.data : json;
    },

    get: (path) => ApiClient._request('GET', path),
    post: (path, body) => ApiClient._request('POST', path, body),
    put: (path, body) => ApiClient._request('PUT', path, body),
    del: (path) => ApiClient._request('DELETE', path),
};
