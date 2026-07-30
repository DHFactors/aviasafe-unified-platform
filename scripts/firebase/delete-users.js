const admin = require('firebase-admin');
const serviceAccount = require('./service-account.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

async function deleteUsers() {
    console.log('Deleting existing users...');

    const uids = [
        'x3u8OUSeLZNnuh3HYI2VF',
        '43EBsyohuiSoKeXC0o1vFC',
        'fBOWEsnb5aVPCEQaK9oN3C'
    ];

    for (const uid of uids) {
        try {
            await admin.auth().deleteUser(uid);
            console.log('✅ Deleted:', uid);
        } catch (error) {
            console.error('❌ Error deleting', uid, ':', error.message);
        }
    }

    console.log('✅ Done!');
}

deleteUsers();