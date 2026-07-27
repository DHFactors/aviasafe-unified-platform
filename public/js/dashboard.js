let chartInstances = {};
let currentPage = 1;
let currentDays = 90;
const PAGE_SIZE = 10;

function waitForFirebase() {
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
}

document.addEventListener('DOMContentLoaded', async () => {
    await waitForFirebase();
    const user = firebase.auth().currentUser;
    if (!user) {
        window.location.href = '/login.html';
        return;
    }

    try {
        const tokenResult = await user.getIdTokenResult();
        const role = tokenResult.claims.role;
        const tenantId = tokenResult.claims.tenant_id;

        if (role !== 'AIRLINE_ADMIN' && role !== 'CAAN_SMD' && role !== 'SUPER_ADMIN') {
            showError('Unauthorized role. Contact your administrator.');
            return;
        }

        document.getElementById('dashboardSection').style.display = 'block';
        document.getElementById('logoutBtn').style.display = 'block';

        const header = document.getElementById('tenantTitle');
        if (tenantId) {
            header.textContent = `${tenantId.toUpperCase()} — Safety Dashboard`;
        } else {
            header.textContent = 'Cross-Tenant Safety Overview';
        }

        if (role === 'AIRLINE_ADMIN' || role === 'CAAN_SMD') {
            document.getElementById('riskMatrixSection').style.display = 'block';
            await loadRiskMatrixConfig();
            setupRiskMatrixForm();
        }
    } catch {
        window.location.href = '/login.html';
        return;
    }

    document.getElementById('logoutBtn').addEventListener('click', async () => {
        await firebase.auth().signOut();
        window.location.href = '/login.html';
    });

    const daysEl = document.getElementById('daysFilter');
    if (daysEl) {
        currentDays = parseInt(daysEl.value, 10);
        daysEl.addEventListener('change', () => {
            currentDays = parseInt(daysEl.value, 10);
            currentPage = 1;
            loadAll();
        });
    }

    document.getElementById('refreshBtn').addEventListener('click', () => {
        currentPage = 1;
        loadAll();
    });

    loadAll();
});

async function loadAll() {
    await Promise.all([
        loadKpis(),
        loadRiskDistribution(),
        loadMonthlyTrends(),
        loadHazardFrequency(),
        loadRecentReports(),
        loadHeatMap(),
    ]);
}

async function loadKpis() {
    const el = document.getElementById('kpiGrid');
    setLoading(el);

    try {
        const data = await DashboardAPI.getOverview(currentDays);
        const k = data.kpis || {};

        el.innerHTML = `
            <div class="kpi-card"><h3>Total Reports</h3><div class="kpi-value">${k.total_reports ?? 0}</div></div>
            <div class="kpi-card"><h3>Open</h3><div class="kpi-value">${k.open_reports ?? 0}</div></div>
            <div class="kpi-card"><h3>Closed</h3><div class="kpi-value">${k.closed_reports ?? 0}</div></div>
            <div class="kpi-card high"><h3>High Risk</h3><div class="kpi-value">${k.high_risk_reports ?? 0}</div></div>
            <div class="kpi-card"><h3>Critical</h3><div class="kpi-value">${k.critical_reports ?? 0}</div></div>
            <div class="kpi-card"><h3>Anon Rate</h3><div class="kpi-value">${k.anonymous_percentage ?? 0}%</div></div>
        `;
        setReady(el);
    } catch (err) {
        setError(el, err.message);
    }
}

async function loadRiskDistribution() {
    const el = document.getElementById('riskChart');
    setLoading(el);

    try {
        const data = await DashboardAPI.getRiskDistribution(currentDays);
        if (!data || data.length === 0) {
            setEmpty(el, 'No risk data available');
            return;
        }
        setReady(el);
        renderRiskChart(data);
    } catch (err) {
        setError(el, err.message);
    }
}

async function loadMonthlyTrends() {
    const el = document.getElementById('trendChart');
    setLoading(el);

    try {
        const data = await DashboardAPI.getMonthlyTrends(currentDays * 2 > 730 ? 730 : currentDays * 2);
        if (!data || data.length === 0) {
            setEmpty(el, 'No trend data available');
            return;
        }
        setReady(el);
        renderTrendChart(data);
    } catch (err) {
        setError(el, err.message);
    }
}

async function loadHazardFrequency() {
    const el = document.getElementById('hazardChart');
    setLoading(el);

    try {
        const data = await DashboardAPI.getHazardFrequency(currentDays);
        if (!data || data.length === 0) {
            setEmpty(el, 'No hazard data available');
            return;
        }
        setReady(el);
        renderHazardChart(data);
    } catch (err) {
        setError(el, err.message);
    }
}

async function loadRecentReports() {
    const el = document.getElementById('reportsTable');
    const pagEl = document.getElementById('pagination');
    setLoading(el);

    try {
        const data = await DashboardAPI.getRecentReports(currentDays, currentPage, PAGE_SIZE);
        if (!data || !data.items || data.items.length === 0) {
            setEmpty(el, 'No reports found');
            pagEl.innerHTML = '';
            return;
        }
        setReady(el);
        renderReportsTable(data.items);
        renderPagination(data, pagEl);
    } catch (err) {
        setError(el, err.message);
    }
}

async function loadHeatMap() {
    const container = document.getElementById('heatMapCanvas');
    try {
        const data = await DashboardAPI.getRecentReports(currentDays, 1, 200);
        if (data && data.items && data.items.length > 0) {
            renderHeatMapFromReports(data.items, container);
        } else {
            container.innerHTML = '<p style="text-align:center;color:#64748b;padding:2rem;">No report data for heat map</p>';
        }
    } catch {
        container.innerHTML = '<p style="text-align:center;color:#64748b;padding:2rem;">Heat map unavailable — load more reports</p>';
    }
}

function renderRiskChart(data) {
    destroyChart('riskChartCanvas');
    const ctx = document.getElementById('riskChartCanvas');
    if (!ctx) return;

    const counts = { Low: 0, Medium: 0, High: 0, 'Very High': 0 };
    for (const d of data) {
        const level = d.risk_level;
        if (counts.hasOwnProperty(level)) counts[level] = d.count;
    }
    const labels = ICAO_RISK_LABELS;
    const vals = labels.map(l => counts[l] || 0);
    const colors = labels.map(l => ICAO_COLORS[l]);

    chartInstances.risk = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Reports',
                data: vals,
                backgroundColor: colors,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.y} (${data[ctx.dataIndex]?.percentage || 0}%)`,
                    },
                },
                legend: { display: false },
            },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });
}

function renderTrendChart(data) {
    destroyChart('trendChartCanvas');
    const ctx = document.getElementById('trendChartCanvas');
    if (!ctx) return;

    chartInstances.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => `${d.month}/${d.year}`),
            datasets: [
                { label: 'Total', data: data.map(d => d.total), borderColor: '#1a73e8', fill: false, tension: 0.3 },
                { label: 'Voluntary', data: data.map(d => d.voluntary), borderColor: '#28a745', fill: false, tension: 0.3 },
                { label: 'Mandatory', data: data.map(d => d.mandatory), borderColor: '#dc3545', fill: false, tension: 0.3 },
                { label: 'High Risk', data: data.map(d => d.high_risk), borderColor: '#fd7e14', fill: false, tension: 0.3, borderDash: [5, 5] },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });
}

function renderHazardChart(data) {
    destroyChart('hazardChartCanvas');
    const ctx = document.getElementById('hazardChartCanvas');
    if (!ctx) return;

    const top = data.slice(0, 10);
    chartInstances.hazard = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(d => d.occurrence_type),
            datasets: [{
                label: 'Occurrences',
                data: top.map(d => d.count),
                backgroundColor: '#1a73e8',
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { beginAtZero: true, ticks: { precision: 0 } },
            },
            plugins: { legend: { display: false } },
        },
    });
}

function renderHeatMapFromReports(reports, container) {
    const counts = {};
    for (const r of reports) {
        const s = r.severity_level;
        const p = r.probability_level;
        if (s >= 1 && s <= 5 && p >= 1 && p <= 5) {
            const key = `${s}x${p}`;
            counts[key] = (counts[key] || 0) + 1;
        }
    }

    const hasData = Object.keys(counts).length > 0;
    if (!hasData) {
        container.innerHTML = '<p style="text-align:center;color:#64748b;padding:2rem;">No ICAO risk data available. Reports submitted with Severity × Probability will appear here.</p>';
        return;
    }

    const heatData = [];
    let maxCount = 0;
    for (let s = 1; s <= 5; s++) {
        for (let p = 1; p <= 5; p++) {
            const c = counts[`${s}x${p}`] || 0;
            heatData.push({ severity: s, probability: p, count: c });
            if (c > maxCount) maxCount = c;
        }
    }
    if (maxCount === 0) maxCount = 1;

    const getColor = (count) => {
        if (count === 0) return '#f1f5f9';
        const ratio = count / maxCount;
        if (ratio < 0.25) return '#e8f5e9';
        if (ratio < 0.5) return '#fff8e1';
        if (ratio < 0.75) return '#fff3e0';
        return '#fde8e8';
    };

    const getTextColor = (count) => (count === 0 ? '#94a3b8' : '#1e293b');

    const getRiskClass = (index) => getRiskBadgeClass(classifyRisk(index));
    const getRiskText = (index) => classifyRisk(index);

    let html = '<table style="border-collapse:collapse;margin:0 auto;font-size:0.85rem;">';
    html += '<tr><td style="padding:0.5rem;font-weight:700;color:#475569;text-align:right;">P\\S</td>';
    for (let s = 1; s <= 5; s++) {
        html += `<td style="padding:0.5rem 0.75rem;font-weight:700;color:#1a73e8;text-align:center;">S=${s}</td>`;
    }
    html += '</tr>';

    for (let p = 5; p >= 1; p--) {
        html += `<tr><td style="padding:0.5rem;font-weight:700;color:#475569;text-align:right;">P=${p}</td>`;
        for (let s = 1; s <= 5; s++) {
            const item = heatData.find(d => d.severity === s && d.probability === p);
            const count = item ? item.count : 0;
            const index = s * p;
            const color = getColor(count);
            html += `<td style="padding:0.5rem;text-align:center;background:${color};border:1px solid #e2e8f0;border-radius:4px;min-width:70px;">
                <div style="font-weight:700;color:${getTextColor(count)};font-size:1.1rem;">${index}</div>
                <div style="font-size:0.65rem;margin-top:0.1rem;"><span class="badge ${getRiskClass(index)}">${getRiskText(index)}</span></div>
                <div style="font-size:0.75rem;color:${getTextColor(count)};margin-top:0.15rem;">${count}</div>
            </td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    html += '<p style="text-align:center;font-size:0.75rem;color:#94a3b8;margin-top:0.75rem;">Severity (columns) × Probability (rows) — Cell color intensity = report count</p>';

    container.innerHTML = html;
}

function renderReportsTable(items) {
    const tbody = document.getElementById('reportsBody');
    tbody.innerHTML = '';

    for (const r of items) {
        const date = r.occurrence_date ? new Date(r.occurrence_date).toLocaleDateString() : '-';
        const riskLevel = r.risk_level || getRiskLevelLabel(r.risk_index).text;
        const riskClass = riskLevel === 'Very High' ? 'badge-critical' : riskLevel === 'High' ? 'badge-high' : riskLevel === 'Medium' ? 'badge-medium' : riskLevel === 'Low' ? 'badge-low' : 'badge-default';
        const statClass = statusBadgeClass(r.status);
        const ri = r.risk_index !== null && r.risk_index !== undefined ? r.risk_index : '-';
        const reportId = r.id;

        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            window.location.href = `/report/detail.html?id=${reportId}`;
        });
        row.innerHTML = `
            <td>${date}</td>
            <td>${r.report_type === 'mandatory' ? 'MOR' : 'VSR'}</td>
            <td>${r.occurrence_type || '-'}</td>
            <td>${r.location || '-'}</td>
            <td style="text-align:center;font-weight:700;">${ri}</td>
            <td><span class="badge ${riskClass}">${riskLevel}</span></td>
            <td><span class="badge ${statClass}">${r.status || 'NEW'}</span></td>
        `;
        tbody.appendChild(row);
    }
}

function renderPagination(data, container) {
    container.innerHTML = '';

    const prev = document.createElement('button');
    prev.textContent = '‹ Prev';
    prev.className = 'page-btn';
    prev.disabled = !data.has_prev;
    prev.addEventListener('click', () => { currentPage--; loadRecentReports(); });

    const next = document.createElement('button');
    next.textContent = 'Next ›';
    next.className = 'page-btn';
    next.disabled = !data.has_next;
    next.addEventListener('click', () => { currentPage++; loadRecentReports(); });

    const info = document.createElement('span');
    info.className = 'page-info';
    info.textContent = `Page ${data.page} of ${data.total_pages} (${data.total} total)`;

    container.appendChild(prev);
    container.appendChild(info);
    container.appendChild(next);
}

function getRiskLevelLabel(index) {
    const level = classifyRisk(index);
    return { text: level, class: getRiskBadgeClass(level) };
}

function severityBadgeClass(sev) {
    switch (sev) {
        case 'Critical': return 'badge-critical';
        case 'High': return 'badge-high';
        case 'Medium': return 'badge-medium';
        case 'Low': return 'badge-low';
        default: return 'badge-default';
    }
}

function statusBadgeClass(status) {
    switch (status) {
        case 'NEW': return 'badge-new';
        case 'PROCESSING': return 'badge-processing';
        case 'COMPLETED': case 'SUBMITTED': return 'badge-completed';
        case 'FAILED': return 'badge-failed';
        case 'ARCHIVED': return 'badge-archived';
        default: return 'badge-default';
    }
}

function destroyChart(key) {
    if (chartInstances[key]) {
        chartInstances[key].destroy();
        delete chartInstances[key];
    }
}

async function loadRiskMatrixConfig() {
    try {
        const config = await getRiskMatrix();
        if (config && config.thresholds) {
            document.getElementById('rmLowMax').value = config.thresholds.low_max || 5;
            document.getElementById('rmMediumMax').value = config.thresholds.medium_max || 9;
            document.getElementById('rmHighMax').value = config.thresholds.high_max || 15;
        }
    } catch {
        // Use defaults
    }
}

function setupRiskMatrixForm() {
    document.getElementById('riskMatrixForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('rmSaveBtn');
        const status = document.getElementById('rmStatus');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        status.style.display = 'none';

        try {
            const lowMax = parseInt(document.getElementById('rmLowMax').value, 10);
            const mediumMax = parseInt(document.getElementById('rmMediumMax').value, 10);
            const highMax = parseInt(document.getElementById('rmHighMax').value, 10);

            if (lowMax >= mediumMax || mediumMax >= highMax) {
                throw new Error('Thresholds must be strictly increasing: Low < Medium < High');
            }
            if (lowMax < 1 || highMax > 25) {
                throw new Error('Values must be between 1 and 25.');
            }

            await updateRiskMatrix({ lowMax, mediumMax, highMax });

            status.style.color = '#2e7d32';
            status.innerHTML = '<i class="fas fa-check-circle"></i> Saved successfully';
            status.style.display = 'inline';
            setTimeout(() => { status.style.display = 'none'; }, 3000);
        } catch (err) {
            status.style.color = '#dc3545';
            status.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + err.message;
            status.style.display = 'inline';
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save"></i> Save Thresholds';
        }
    });
}

function setLoading(el) {
    el.dataset.state = 'loading';
    el.classList.remove('state-ready', 'state-empty', 'state-error');
    el.classList.add('state-loading');
}

function setReady(el) {
    el.dataset.state = 'ready';
    el.classList.remove('state-loading', 'state-empty', 'state-error');
    el.classList.add('state-ready');
}

function setEmpty(el, msg) {
    el.dataset.state = 'empty';
    el.classList.remove('state-loading', 'state-ready', 'state-error');
    el.classList.add('state-empty');
    if (!el.querySelector('.empty-msg')) {
        const p = document.createElement('p');
        p.className = 'empty-msg';
        p.textContent = msg;
        el.appendChild(p);
    }
}

function setError(el, msg) {
    el.dataset.state = 'error';
    el.classList.remove('state-loading', 'state-ready', 'state-empty');
    el.classList.add('state-error');
    let errEl = el.querySelector('.error-msg');
    if (!errEl) {
        errEl = document.createElement('p');
        errEl.className = 'error-msg';
        el.appendChild(errEl);
    }
    errEl.textContent = `Error: ${msg}`;
}

function showError(msg) {
    document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;font-family:sans-serif;">
            <h2 style="color:#dc3545;">Access Denied</h2>
            <p>${msg}</p>
            <a href="/login.html" style="margin-top:1rem;color:#1a73e8;">Return to Login</a>
        </div>
    `;
}
