const DiversionsAPI = {
    list: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.status) qs.set('status', params.status);
        if (params.reason) qs.set('reason', params.reason);
        if (params.aircraft) qs.set('aircraft', params.aircraft);
        if (params.search) qs.set('search', params.search);
        return ApiClient.get(`/api/flight-diversions?${qs.toString()}`);
    },

    get: (id) => ApiClient.get(`/api/flight-diversions/${id}`),

    create: (data) => ApiClient.post('/api/flight-diversions', data),

    update: (id, data) => ApiClient._request('PATCH', `/api/flight-diversions/${id}`, data),

    delete: (id) => ApiClient.del(`/api/flight-diversions/${id}`),

    getStats: () => ApiClient.get('/api/flight-diversions/stats'),

    linkToHazard: (diversionId, hazardId) =>
        ApiClient._request('POST', `/api/flight-diversions/${diversionId}/link-hazard?hazard_id=${encodeURIComponent(hazardId)}`),

    unlinkFromHazard: (diversionId) =>
        ApiClient._request('DELETE', `/api/flight-diversions/${diversionId}/link-hazard`),
};

const DIVERSION_REASONS = [
    'Weather', 'Technical', 'Medical', 'Fuel', 'Security',
    'Operational', 'Airport Closure', 'Air Traffic Control', 'Other'
];

const DIVERSION_STATUSES = ['Pending', 'Reviewed', 'Investigating', 'Closed', 'Linked to Hazard'];

function diversionStatusBadgeClass(status) {
    const map = {
        'Pending': 'badge-new',
        'Reviewed': 'badge-processing',
        'Investigating': 'badge-warning',
        'Closed': 'badge-completed',
        'Linked to Hazard': 'badge-critical'
    };
    return map[status] || 'badge-default';
}

function diversionReasonBadgeClass(reason) {
    const map = {
        'Weather': 'badge-info',
        'Technical': 'badge-high',
        'Medical': 'badge-critical',
        'Fuel': 'badge-warning',
        'Security': 'badge-danger',
        'Operational': 'badge-processing',
        'Airport Closure': 'badge-default',
        'Air Traffic Control': 'badge-medium',
        'Other': 'badge-default'
    };
    return map[reason] || 'badge-default';
}

function formatDiversionDate(d) {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return '-'; }
}
