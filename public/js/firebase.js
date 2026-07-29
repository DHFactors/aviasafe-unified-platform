/* ============================================================================
   FILE: firebase.js
   PATH: public/js/firebase.js
   VERSION: 2.0.0
   DATE CREATED: 2026-07-26
   DATE REVISED: 2026-07-26
   PURPOSE: Firebase client SDK initialization.
            Loads Firebase SDK dynamically and initializes services.
   AUTHOR: AviaSAFE Systems
   ============================================================================ */

// ============================================================================
// FIREBASE CONFIGURATION
// ============================================================================

const firebaseConfig = {
    apiKey: "AIzaSyAhvyNyLyqRWidGIkk-by3J9bJ5xtSFTdc",
    authDomain: "gap-analysis-ssp.firebaseapp.com",
    projectId: "gap-analysis-ssp",
    storageBucket: "gap-analysis-ssp.appspot.com",
    messagingSenderId: "817614332543",
    appId: "1:817614332543:web:01224a312e8478b24d554a"
};

// Centralized application configuration (single source of truth)
const APP_CONFIG = {
    apiBaseUrl: 'https://aviasafe-unified-platform.onrender.com',
    environment: 'production',
    pagination: { defaultPageSize: 20, maxPageSize: 100 },
};

window.APP_CONFIG = APP_CONFIG;
window.API_BASE_URL = APP_CONFIG.apiBaseUrl;
window.__FIREBASE_CONFIG__ = firebaseConfig;

// ============================================================================
// DYNAMIC LOADING OF FIREBASE SDK
// ============================================================================

function loadFirebaseSDK() {
    return new Promise((resolve, reject) => {
        // Check if Firebase is already loaded
        if (typeof firebase !== 'undefined' && firebase.initializeApp) {
            resolve(firebase);
            return;
        }

        // Load Firebase App SDK
        const scriptApp = document.createElement('script');
        scriptApp.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js';
        scriptApp.async = true;
        scriptApp.onload = function() {
            // Load Firestore SDK
            const scriptFirestore = document.createElement('script');
            scriptFirestore.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-firestore-compat.js';
            scriptFirestore.async = true;
            scriptFirestore.onload = function() {
                // Load Auth SDK
                const scriptAuth = document.createElement('script');
                scriptAuth.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js';
                scriptAuth.async = true;
                scriptAuth.onload = function() {
                    // Load Storage SDK (optional)
                    const scriptStorage = document.createElement('script');
                    scriptStorage.src = 'https://www.gstatic.com/firebasejs/9.22.0/firebase-storage-compat.js';
                    scriptStorage.async = true;
                    scriptStorage.onload = function() {
                        initializeFirebase();
                        resolve(firebase);
                    };
                    scriptStorage.onerror = function() {
                        // Storage is optional, still resolve
                        initializeFirebase();
                        resolve(firebase);
                    };
                    document.head.appendChild(scriptStorage);
                };
                scriptAuth.onerror = function() {
                    // Auth is optional, still resolve
                    initializeFirebase();
                    resolve(firebase);
                };
                document.head.appendChild(scriptAuth);
            };
            scriptFirestore.onerror = function() {
                // Firestore is optional, still resolve
                initializeFirebase();
                resolve(firebase);
            };
            document.head.appendChild(scriptFirestore);
        };
        scriptApp.onerror = function() {
            reject(new Error('Failed to load Firebase SDK'));
        };
        document.head.appendChild(scriptApp);
    });
}

function initializeFirebase() {
    if (typeof firebase !== 'undefined' && firebase.initializeApp) {
        try {
            // Check if already initialized
            if (!firebase.apps || firebase.apps.length === 0) {
                firebase.initializeApp(firebaseConfig);
                console.log('✅ Firebase initialized successfully');
            } else {
                console.log('ℹ️ Firebase already initialized');
            }
        } catch (error) {
            console.warn('Firebase initialization error:', error);
        }
    } else {
        console.warn('⚠️ Firebase SDK not available');
    }
}

// ============================================================================
// INITIALIZE SERVICES
// ============================================================================

let auth = null;
let db = null;

function initServices() {
    if (typeof firebase !== 'undefined' && firebase.apps && firebase.apps.length > 0) {
        try {
            auth = firebase.auth();
            db = firebase.firestore();
            
            console.log('✅ Firebase services initialized');
        } catch (error) {
            console.warn('Error initializing Firebase services:', error);
        }
    } else {
        console.warn('⚠️ Cannot initialize services - Firebase not available');
    }
}

// ============================================================================
// LOAD AND INITIALIZE
// ============================================================================

// Auto-initialize when loaded
(function() {
    // Check if Firebase is already available (from CDN in HTML)
    if (typeof firebase !== 'undefined' && firebase.initializeApp) {
        initializeFirebase();
        initServices();
        window.firebase = firebase;
        window.auth = auth;
        window.db = db;
        console.log('✅ Firebase loaded from CDN');
    } else {
        // Load dynamically
        loadFirebaseSDK()
            .then(function() {
                initServices();
                window.firebase = firebase;
                window.auth = auth;
                window.db = db;
                console.log('✅ Firebase loaded dynamically');
            })
            .catch(function(error) {
                console.warn('⚠️ Firebase load failed:', error.message);
                window.firebase = null;
                window.auth = null;
                window.db = null;
            });
    }
})();

// ============================================================================
// SHARED AUTH HELPERS (used by all pages)
// ============================================================================

function waitForFirebase() {
    return new Promise(function(resolve) {
        if (typeof firebase !== 'undefined' && firebase.auth) {
            resolve();
            return;
        }
        var check = setInterval(function() {
            if (typeof firebase !== 'undefined' && firebase.auth) {
                clearInterval(check);
                resolve();
            }
        }, 30);
        setTimeout(function() {
            clearInterval(check);
            resolve();
        }, 10000);
    });
}

async function getCurrentUser() {
    await waitForFirebase();
    return new Promise(function(resolve) {
        var resolved = false;
        var unsubscribe = firebase.auth().onAuthStateChanged(async function(user) {
            if (resolved) return;
            if (!user) return;
            resolved = true;
            unsubscribe();
            try {
                var tokenResult = await user.getIdTokenResult(true);
                var claims = tokenResult.claims || {};
                resolve({
                    uid: user.uid,
                    email: user.email,
                    role: claims.role || 'USER',
                    tenantId: claims.tenant_id || null,
                    claims: claims
                });
            } catch (error) {
                resolve(null);
            }
        });
        setTimeout(function() {
            if (!resolved) {
                resolved = true;
                unsubscribe();
                resolve(null);
            }
        }, 5000);
    });
}

console.log('📦 firebase.js loaded');