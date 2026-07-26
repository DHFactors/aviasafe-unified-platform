const admin = require('firebase-admin');
const serviceAccount = require('./service-account.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

async function verifyClaims() {
    console.log('Verifying user claims...\n');

    const users = [
        { uid: 'Z3uNhvyEP2RKBnwtXUowqFMy3Cg1', email: 'admin@aviasafesystems.com' },
        { uid: 'pl1YEWCBq5OC4rx8SNbOV9zVFwC2', email: 'sal@aviasafesystems.com' },
        { uid: 'n46U3TB2wVXVkYqYpTwazps8Zx73', email: 'salsafety@aviasafesystems.com' },
        { uid: 'WHmIerlq8sQCAjFtD1XNz6etRRg1', email: 'smd@caanepal.gov.np' }
    ];

    for (const user of users) {
        try {
            const userRecord = await admin.auth().getUser(user.uid);
            console.log('📧', user.email);
            console.log('   UID:', user.uid);
            console.log('   Claims:', JSON.stringify(userRecord.customClaims || {}));
            console.log('   ---');
        } catch (error) {
            console.error('❌ Error for', user.email, ':', error.message);
        }
    }

    console.log('\n✅ Done!');
}

verifyClaims();