# ============================================================================
# FILE: firebase.py
# PATH: backend/app/firebase.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-03
# PURPOSE: Firebase Admin SDK integration for Firestore and Auth.
#          Provides secure access to the unified aviasafe-platform database.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import Optional, Dict, Any, List
from loguru import logger

# Firebase Admin SDK initialization
_firebase_app = None
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    global _firebase_app, _db
    
    if not firebase_admin._apps:
        try:
            # Get credentials from environment
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            private_key = os.getenv("FIREBASE_PRIVATE_KEY")
            client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
            
            if not all([project_id, private_key, client_email]):
                raise ValueError("Missing Firebase credentials in environment")
            
            # Create credentials dict
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key.replace('\\n', '\n'),
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            _db = firestore.client()
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    else:
        _db = firestore.client()
    
    return _firebase_app

def get_db():
    """Get Firestore database client."""
    if _db is None:
        initialize_firebase()
    return _db

def get_auth():
    """Get Firebase Auth client."""
    if _firebase_app is None:
        initialize_firebase()
    return auth

def get_tenant_collection(tenant_id: str, collection: str):
    """Get a tenant-isolated collection reference.
    
    Args:
        tenant_id: The tenant/organization ID
        collection: The sub-collection name (responses, reports, etc.)
    
    Returns:
        Firestore collection reference
    """
    db = get_db()
    return db.collection('tenants').document(tenant_id).collection(collection)

def get_cross_tenant_collection(collection: str):
    """Get collection across all tenants (for CAAN SMD access).
    
    Args:
        collection: The collection name to query across all tenants
    
    Returns:
        Firestore collection group reference
    """
    db = get_db()
    return db.collection_group(collection)

def get_tenant_metadata(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get tenant metadata document."""
    db = get_db()
    doc = db.collection('tenants').document(tenant_id).collection('metadata').document('info').get()
    if doc.exists:
        return doc.to_dict()
    return None

def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return decoded claims."""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

def create_custom_claims(uid: str, role: str, tenant_id: Optional[str] = None) -> bool:
    """Set custom claims for a user."""
    try:
        claims = {"role": role}
        if tenant_id:
            claims["tenant_id"] = tenant_id
        auth.set_custom_user_claims(uid, claims)
        logger.info(f"Custom claims set for user {uid}: {claims}")
        return True
    except Exception as e:
        logger.error(f"Failed to set custom claims: {e}")
        return False