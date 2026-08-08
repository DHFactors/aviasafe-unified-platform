const CanCapAPI = {
    // CAN
    listCans: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.hazard_id) qs.set('hazard_id', params.hazard_id);
        if (params.status) qs.set('status', params.status);
        if (params.priority) qs.set('priority', params.priority);
        if (params.assigned_to) qs.set('assigned_to', params.assigned_to);
        if (params.search) qs.set('search', params.search);
        return ApiClient.get(`/api/cans?${qs.toString()}`);
    },

    getCan: (canId) => ApiClient.get(`/api/cans/${canId}`),

    issueCan: (data) => ApiClient.post('/api/cans', data),

    updateCanStatus: (canId, status) =>
        ApiClient._request('PATCH', `/api/cans/${canId}/status?status=${status}`),

    deleteCan: (canId) => ApiClient.del(`/api/cans/${canId}`),

    getStats: () => ApiClient.get('/api/cans/stats'),

    // CAP
    submitCap: (canId, data) => ApiClient.post(`/api/cans/${canId}/caps`, data),

    listCaps: (canId) => ApiClient.get(`/api/cans/${canId}/caps`),

    listAllCaps: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.status) qs.set('status', params.status);
        if (params.can_id) qs.set('can_id', params.can_id);
        if (params.search) qs.set('search', params.search);
        return ApiClient.get(`/api/cans/caps?${qs.toString()}`);
    },

    getCap: (capId) => ApiClient.get(`/api/cans/caps/${capId}`),

    updateCap: (capId, data) => ApiClient.patch ? ApiClient._request('PATCH', `/api/cans/caps/${capId}`, data) : ApiClient.put(`/api/cans/caps/${capId}`, data),

    reviewCap: (capId, data) => ApiClient._request('PATCH', `/api/cans/caps/${capId}/review`, data),

    updateCapStatus: (capId, status) =>
        ApiClient._request('PATCH', `/api/cans/caps/${capId}/status?status=${status}`),
};

const CAN_STATUSES = ['Open', 'Under Review', 'Closed', 'Escalated'];
const CAN_PRIORITIES = ['High', 'Medium', 'Low'];
const CAP_STATUSES = ['In Progress', 'Under Review', 'Completed', 'Revision Required', 'Overdue'];

function canStatusBadgeClass(status) {
    const map = { 'Open': 'badge-new', 'Under Review': 'badge-warning', 'Closed': 'badge-completed', 'Escalated': 'badge-danger' };
    return map[status] || 'badge-default';
}

function capStatusBadgeClass(status) {
    const map = {
        'In Progress': 'badge-processing',
        'Under Review': 'badge-warning',
        'Completed': 'badge-completed',
        'Revision Required': 'badge-critical',
        'Overdue': 'badge-danger'
    };
    return map[status] || 'badge-default';
}

function canPriorityBadgeClass(priority) {
    const map = { 'High': 'badge-critical', 'Medium': 'badge-warning', 'Low': 'badge-low' };
    return map[priority] || 'badge-default';
}

function formatCanDate(d) {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return '-'; }
}

ApiClient.patch = function(path, body) {
    return ApiClient._request('PATCH', path, body);
};
