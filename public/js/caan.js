const firebaseConfig = {
    apiKey: "AIzaSyBq9gFgQ-R5M9xkxyg9X_pzW2xP0VwQ5Ow",
    authDomain: "gap-analysis-ssp.firebaseapp.com",
    projectId: "gap-analysis-ssp",
    storageBucket: "gap-analysis-ssp.appspot.com",
    messagingSenderId: "817614332543",
    appId: "1:817614332543:web:01224a312e8478b24d554a"
};

let db, auth;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js");
        const { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js");
        const { getFirestore } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js");

        const app = initializeApp(firebaseConfig);
        auth = getAuth(app);
        db = getFirestore(app);

        bindEvents(signInWithEmailAndPassword, signOut);
        monitorAuthState(onAuthStateChanged);
    } catch (e) {
        console.error("Firebase SDK initialization failure: ", e);
    }
});

function bindEvents(signInWithEmailAndPassword, signOut) {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    loginBtn.addEventListener('click', async () => {
        const email = document.getElementById('emailInput').value.trim();
        const password = document.getElementById('passwordInput').value;
        const msg = document.getElementById('authMessage');

        msg.textContent = "Authenticating...";
        msg.style.color = "var(--navy)";

        try {
            await signInWithEmailAndPassword(auth, email, password);
        } catch (error) {
            msg.style.color = "var(--alert)";
            msg.textContent = "Authentication Failed. Please check your credentials.";
        }
    });

    logoutBtn.addEventListener('click', async () => {
        await signOut(auth);
        window.location.reload();
    });
}

function monitorAuthState(onAuthStateChanged) {
    onAuthStateChanged(auth, (user) => {
        if (user) {
            const claims = user.reload ? null : null;
            user.getIdTokenResult().then((idTokenResult) => {
                if (idTokenResult.claims.role === 'CAAN_SMD') {
                    loadDashboardUI();
                    fetchAggregatedSSPData();
                } else {
                    document.getElementById('authMessage').textContent = "Unauthorized. CAAN SMD role required.";
                    document.getElementById('authMessage').style.color = "var(--alert)";
                }
            }).catch(() => {
                document.getElementById('authMessage').textContent = "Error verifying credentials.";
                document.getElementById('authMessage').style.color = "var(--alert)";
            });
        } else {
            document.getElementById('authSection').style.display = 'block';
            document.getElementById('dashboardSection').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'none';
        }
    });
}

function loadDashboardUI() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('logoutBtn').style.display = 'block';
}

function fetchAggregatedSSPData() {
    const tbody = document.getElementById('sspBody');
    tbody.innerHTML = '';

    const operators = [
        { name: "SITA AIR", p1: 82, p2: 76, p3: 88, p4: 71, count: 45 },
        { name: "TARA AIR", p1: 88, p2: 81, p3: 84, p4: 79, count: 62 },
        { name: "SUMMIT AIR", p1: 75, p2: 68, p3: 72, p4: 65, count: 28 },
        { name: "BUDDHA AIR", p1: 92, p2: 89, p3: 94, p4: 85, count: 110 }
    ];

    const getScoreClass = (score) => {
        if (score >= 85) return 'score-high';
        if (score >= 70) return 'score-mid';
        return 'score-low';
    };

    operators.forEach(op => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${op.name}</td>
            <td class="${getScoreClass(op.p1)}">${op.p1}%</td>
            <td class="${getScoreClass(op.p2)}">${op.p2}%</td>
            <td class="${getScoreClass(op.p3)}">${op.p3}%</td>
            <td class="${getScoreClass(op.p4)}">${op.p4}%</td>
            <td style="color: #64748B;">${op.count} reports</td>
        `;
        tbody.appendChild(row);
    });
}
