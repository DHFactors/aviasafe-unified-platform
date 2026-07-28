const ReportsAPI = {
    // Quarterly
    generateQuarterly: (year, quarter) => {
        const qs = `year=${year}&quarter=${quarter}`;
        return ApiClient.post(`/api/reporting/quarterly?${qs}`);
    },

    listQuarterly: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.year) qs.set('year', params.year);
        if (params.tenant_id) qs.set('tenant_id', params.tenant_id);
        return ApiClient.get(`/api/reporting/quarterly?${qs.toString()}`);
    },

    getQuarterly: (reportId) =>
        ApiClient.get(`/api/reporting/quarterly/${reportId}`),

    exportQuarterly: (reportId) =>
        ApiClient._request('GET', `/api/reporting/quarterly/${reportId}/export`),

    // Annual
    generateAnnual: (year) => {
        const qs = `year=${year}`;
        return ApiClient.post(`/api/reporting/annual?${qs}`);
    },

    listAnnual: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.year) qs.set('year', params.year);
        if (params.tenant_id) qs.set('tenant_id', params.tenant_id);
        return ApiClient.get(`/api/reporting/annual?${qs.toString()}`);
    },

    getAnnual: (reportId) =>
        ApiClient.get(`/api/reporting/annual/${reportId}`),

    exportAnnual: (reportId) =>
        ApiClient._request('GET', `/api/reporting/annual/${reportId}/export`),
};

function formatReportDate(d) {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return '-'; }
}

function reportStatusBadgeClass(status) {
    const map = { 'completed': 'badge-completed', 'generating': 'badge-warning', 'draft': 'badge-default', 'failed': 'badge-critical' };
    return map[status] || 'badge-default';
}

async function downloadPdf(reportId, type) {
    try {
        const token = await ApiClient._getToken();
        const baseUrl = ApiClient._baseUrl();
        const url = `${baseUrl}/api/reporting/${type}/${reportId}/export`;
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) throw new Error('Download failed');
        const blob = await response.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${type}_report_${reportId}.pdf`;
        a.click();
        URL.revokeObjectURL(a.href);
    } catch (err) {
        alert('Error downloading PDF: ' + err.message);
    }
}
