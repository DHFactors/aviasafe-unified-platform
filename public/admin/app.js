/* ============================================================================
   FILE: app.js (SIMPLIFIED - NO LOOP)
   PATH: public/admin/app.js
   VERSION: 3.0.0
   PURPOSE: Super Admin Portal - No redirect loops
   ============================================================================ */

// ============================================================================
// STATE
// ============================================================================

var tenants = [];
var deleteTarget = null;

// ============================================================================
// INIT
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin portal loaded');

    // Check if Firebase is available
    if (typeof firebase === 'undefined') {
        console.error('Firebase not loaded!');
        return;
    }

    // Check if user is logged in
    var user = firebase.auth().currentUser;
    
    if (!user) {
        console.log('No user found. Redirecting to login...');
        // Use replace to prevent back button loop
        window.location.replace('/login.html?tenant=admin');
        return;
    }

    // Check if user has SUPER_ADMIN role
    user.getIdTokenResult()
        .then(function(tokenResult) {
            var claims = tokenResult.claims || {};
            console.log('User claims:', claims);
            
            if (claims.role === 'SUPER_ADMIN') {
                console.log('✅ SUPER_ADMIN - Loading tenants...');
                document.getElementById('adminStatus').textContent = '✅ SUPER_ADMIN';
                loadTenants();
            } else {
                console.log('Not SUPER_ADMIN. Role:', claims.role);
                document.getElementById('adminStatus').textContent = '⚠️ Role: ' + claims.role;
                // Show error instead of redirecting
                document.getElementById('tenantListContainer').innerHTML = 
                    '<div class="empty-state"><i class="fas fa-lock" style="color: var(--color-danger);"></i><p>Access Denied. SUPER_ADMIN role required.</p><p>Your role: ' + claims.role + '</p></div>';
            }
        })
        .catch(function(error) {
            console.error('Auth error:', error);
            document.getElementById('tenantListContainer').innerHTML = 
                '<div class="empty-state"><i class="fas fa-exclamation-triangle" style="color: var(--color-danger);"></i><p>Auth Error: ' + error.message + '</p></div>';
        });

    // Setup forms
    document.getElementById('tenantForm').addEventListener('submit', handleCreateTenant);
});

// ============================================================================
// LOAD TENANTS
// ============================================================================

async function loadTenants() {
    var container = document.getElementById('tenantListContainer');
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading tenants...</div>';

    try {
        var snapshot = await firebase.firestore().collection('tenants').get();

        if (snapshot.empty) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-building"></i><p>No tenants found. Create your first tenant above!</p></div>';
            return;
        }

        tenants = [];
        snapshot.forEach(function(doc) {
            var data = doc.data();
            tenants.push({ 
                id: doc.id, 
                name: data.name, 
                icao: data.icao, 
                country: data.country, 
                active: data.active !== false, 
                createdAt: data.createdAt 
            });
        });

        renderTenantTable(tenants);

    } catch (error) {
        console.error('Error loading tenants:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle" style="color: var(--color-danger);"></i><p>Error loading tenants: ' + error.message + '</p></div>';
    }
}

// ============================================================================
// RENDER TENANT TABLE
// ============================================================================

function renderTenantTable(tenants) {
    var container = document.getElementById('tenantListContainer');

    if (tenants.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-building"></i><p>No tenants found.</p></div>';
        return;
    }

    var html = '<table class="tenant-table"><thead><tr><th>Tenant ID</th><th>Organization</th><th>ICAO</th><th>Country</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>';

    tenants.forEach(function(tenant) {
        var createdDate = tenant.createdAt ? new Date(tenant.createdAt).toLocaleDateString() : 'N/A';
        var isActive = tenant.active !== false;

        html += '<tr>';
        html += '<td><code>' + tenant.id + '</code></td>';
        html += '<td><strong>' + (tenant.name || tenant.id) + '</strong></td>';
        html += '<td>' + (tenant.icao || '-') + '</td>';
        html += '<td>' + (tenant.country || '-') + '</td>';
        html += '<td><span class="status-badge ' + (isActive ? 'status-active' : 'status-inactive') + '">' + (isActive ? 'Active' : 'Inactive') + '</span></td>';
        html += '<td>' + createdDate + '</td>';
        html += '<td><div class="actions">';
        html += '<button class="btn btn-warning btn-sm" onclick="toggleTenant(\'' + tenant.id + '\', ' + (!isActive) + ')"><i class="fas ' + (isActive ? 'fa-pause' : 'fa-play') + '"></i> ' + (isActive ? 'Deactivate' : 'Activate') + '</button>';
        html += '<button class="btn btn-success btn-sm" onclick="generateDummyResponses(\'' + tenant.id + '\')"><i class="fas fa-database"></i> Dummy</button>';
        html += '<button class="btn btn-danger btn-sm" onclick="confirmDelete(\'' + tenant.id + '\')"><i class="fas fa-trash"></i></button>';
        html += '</div></td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ============================================================================
// CREATE TENANT
// ============================================================================

async function handleCreateTenant(e) {
    e.preventDefault();

    var tenantId = document.getElementById('tenantId').value.trim().toLowerCase();
    var name = document.getElementById('tenantName').value.trim();
    var icao = document.getElementById('tenantICAO').value.trim().toUpperCase();
    var country = document.getElementById('tenantCountry').value.trim() || 'Nepal';
    var active = document.getElementById('tenantActive').value === 'true';

    if (!tenantId || !name || !icao) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    if (tenants.find(function(t) { return t.id === tenantId; })) {
        showToast('Tenant "' + tenantId + '" already exists!', 'error');
        return;
    }

    try {
        await firebase.firestore().collection('tenants').doc(tenantId).set({
            name: name,
            icao: icao,
            country: country,
            active: active,
            createdAt: new Date().toISOString()
        });

        showToast('✅ Tenant "' + tenantId + '" created successfully!', 'success');
        document.getElementById('tenantForm').reset();
        document.getElementById('tenantActive').value = 'true';

        await loadTenants();

    } catch (error) {
        console.error('Error creating tenant:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// TOGGLE TENANT
// ============================================================================

async function toggleTenant(tenantId, newStatus) {
    try {
        await firebase.firestore().collection('tenants').doc(tenantId).update({ active: newStatus });
        showToast('Tenant "' + tenantId + '" ' + (newStatus ? 'activated' : 'deactivated'), 'success');
        await loadTenants();
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// DELETE TENANT
// ============================================================================

function confirmDelete(tenantId) {
    var tenant = tenants.find(function(t) { return t.id === tenantId; });
    if (!tenant) return;

    deleteTarget = tenantId;
    document.getElementById('deleteTenantName').textContent = (tenant.name || tenantId) + ' (' + tenantId + ')';
    document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteTarget = null;
}

document.getElementById('confirmDeleteBtn').addEventListener('click', async function() {
    if (!deleteTarget) return;

    try {
        await firebase.firestore().collection('tenants').doc(deleteTarget).delete();
        showToast('🗑️ Tenant "' + deleteTarget + '" deleted successfully', 'success');
        closeDeleteModal();
        await loadTenants();
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
        closeDeleteModal();
    }
});

// ============================================================================
// DUMMY RESPONSE GENERATOR
// ============================================================================

async function generateDummyResponses(tenantId) {
    if (!tenantId) {
        showToast('No tenant selected', 'error');
        return;
    }

    if (!confirm('Generate 25-50 dummy survey responses for ' + tenantId + '?')) {
        return;
    }

    try {
        var count = Math.floor(Math.random() * 25) + 25;
        var responsesRef = firebase.firestore().collection('tenants').doc(tenantId).collection('responses');

        var likertOptions = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];
        var names = ['John Doe', 'Jane Smith', 'Capt. Rajesh', 'First Officer Sunita', 'Engineer Amit', 'ATC Kumar', 'Ground Ops Priya', 'Cabin Crew Maya'];
        var designations = ['Pilot', 'First Officer', 'Engineer', 'ATC', 'Ground Staff', 'Cabin Crew'];
        var departments = ['Flight Ops', 'Maintenance', 'ATC', 'Ground Handling', 'Cabin Services'];

        for (var i = 0; i < count; i++) {
            var answers = [];
            for (var j = 0; j < 20; j++) {
                if (j === 0) {
                    answers.push(Math.random() > 0.2 ? 'Aware' : 'Unaware');
                } else if (j === 19) {
                    answers.push(Math.random() > 0.7 ? 'Great safety culture. Would like more training.' : '');
                } else {
                    answers.push(likertOptions[Math.floor(Math.random() * likertOptions.length)]);
                }
            }

            await responsesRef.add({
                answers: answers,
                respondentInfo: {
                    name: names[Math.floor(Math.random() * names.length)],
                    designation: designations[Math.floor(Math.random() * designations.length)],
                    department: departments[Math.floor(Math.random() * departments.length)]
                },
                submittedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
                isAnonymous: Math.random() > 0.5
            });
        }

        showToast('✅ Generated ' + count + ' dummy responses for ' + tenantId, 'success');
        await loadTenants();

    } catch (error) {
        console.error('Error generating dummy responses:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================

function showToast(message, type) {
    type = type || 'info';
    var container = document.getElementById('toastContainer');
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(function() { toast.remove(); }, 500);
    }, 4000);
}

// ============================================================================
// LOGOUT
// ============================================================================

function logout() {
    firebase.auth().signOut().then(function() {
        window.location.href = '/';
    }).catch(function(error) {
        console.error('Logout error:', error);
    });
}
