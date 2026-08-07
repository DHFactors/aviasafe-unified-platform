/* ============================================================================
   FILE: admin.js
   PATH: public/js/admin.js
   PURPOSE: Shared Super-Admin panel helpers — role guard, authenticated API
            calls, setup-key handling, toasts, small DOM utilities.
   AUTHOR: AviaSAFE Systems
   ============================================================================ */

(function (global) {
    'use strict';

    // ========================================================================
    // AUTH GUARD — requires SUPER_ADMIN, redirects to /admin/login.html
    // ========================================================================

    async function requireAdmin() {
        await waitForFirebase();
        const user = await getCurrentUser();
        if (!user) {
            global.location.href = '/admin/login.html';
            return null;
        }
        if (user.role !== 'SUPER_ADMIN') {
            global.alert('Access denied. SUPER_ADMIN role required.');
            global.location.href = '/';
            return null;
        }
        return user;
    }

    // ========================================================================
    // API — uses the shared ApiClient (auto token + 401 redirect)
    // ========================================================================

    async function apiGet(path) {
        const data = await ApiClient.get(path);
        if (!data) throw new Error('Request failed');
        return data;
    }

    async function apiPost(path, body) {
        const data = await ApiClient.post(path, body);
        if (!data) throw new Error('Request failed');
        return data;
    }

    // ========================================================================
    // SETUP KEY — stored in sessionStorage for this tab only
    // ========================================================================

    function getSetupKey() {
        return global.sessionStorage.getItem('aviasafe_setup_key') || '';
    }

    function setSetupKey(value) {
        if (value) global.sessionStorage.setItem('aviasafe_setup_key', value.trim());
        else global.sessionStorage.removeItem('aviasafe_setup_key');
    }

    function ensureSetupKey() {
        const key = getSetupKey();
        if (key) return key;
        const entered = global.prompt('Enter the admin setup key (SETUP_SECRET) to perform this action:');
        if (!entered) throw new Error('Setup key required');
        setSetupKey(entered);
        return entered.trim();
    }

    // ========================================================================
    // UI HELPERS
    // ========================================================================

    function esc(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function toast(message, type) {
        type = type || 'info';
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:1000;';
            document.body.appendChild(container);
        }
        const el = document.createElement('div');
        el.style.cssText = 'padding:12px 20px;margin-bottom:10px;border-radius:6px;color:#fff;' +
            'box-shadow:0 2px 10px rgba(0,0,0,0.15);background:' +
            (type === 'success' ? '#34a853' : type === 'error' ? '#ea4335' : '#1a6b8a') + ';';
        el.textContent = message;
        container.appendChild(el);
        setTimeout(function () { el.style.opacity = '0'; el.style.transition = 'opacity 0.4s'; setTimeout(function () { el.remove(); }, 400); }, 4000);
    }

    function fmtDate(value) {
        if (!value) return '—';
        const d = new Date(value);
        if (isNaN(d.getTime())) return '—';
        return d.toLocaleString();
    }

    global.AdminUI = {
        requireAdmin: requireAdmin,
        apiGet: apiGet,
        apiPost: apiPost,
        getSetupKey: getSetupKey,
        setSetupKey: setSetupKey,
        ensureSetupKey: ensureSetupKey,
        esc: esc,
        toast: toast,
        fmtDate: fmtDate,
    };
})(window);
