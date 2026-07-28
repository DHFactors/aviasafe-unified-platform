const VerificationAPI = {
    // Verifications
    createVerification: (hazardId, data) =>
        ApiClient.post(`/api/verification/hazards/${hazardId}/verifications`, data),

    listVerifications: (hazardId) =>
        ApiClient.get(`/api/verification/hazards/${hazardId}/verifications`),

    getVerification: (verificationId) =>
        ApiClient.get(`/api/verification/verifications/${verificationId}`),

    getStats: () =>
        ApiClient.get('/api/verification/verifications/stats'),

    // Closure
    createClosure: (hazardId, data) =>
        ApiClient.post(`/api/verification/hazards/${hazardId}/closure`, data),

    getClosure: (hazardId) =>
        ApiClient.get(`/api/verification/hazards/${hazardId}/closure`),

    // Reopen
    reopenHazard: (hazardId, reason) =>
        ApiClient._request('PATCH', `/api/verification/hazards/${hazardId}/reopen?reason=${encodeURIComponent(reason)}`),
};

const VERIFICATION_OUTCOMES = ['Accepted', 'Revision Required', 'Ineffective', 'Overdue'];

function verificationOutcomeBadgeClass(outcome) {
    const map = {
        'Accepted': 'badge-completed',
        'Revision Required': 'badge-warning',
        'Ineffective': 'badge-critical',
        'Overdue': 'badge-danger'
    };
    return map[outcome] || 'badge-default';
}

function formatVerificationDate(d) {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return '-'; }
}
