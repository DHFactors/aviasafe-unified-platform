# ============================================================================
# FILE: auth.py
# PATH: backend/app/middleware/auth.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-03
# PURPOSE: Authentication middleware for FastAPI routes.
#          Verifies Firebase ID tokens and extracts user claims.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.firebase import verify_firebase_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current user from Firebase ID token."""
    token = credentials.credentials
    decoded_token = verify_firebase_token(token)
    
    if not decoded_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract custom claims
    claims = decoded_token.get('claims', {})
    
    return {
        "uid": decoded_token['uid'],
        "email": decoded_token.get('email', ''),
        "role": claims.get('role', 'USER'),
        "tenant_id": claims.get('tenant_id'),
        "claims": claims
    }

async def get_tenant_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user and ensure they have a tenant."""
    if not user.get('tenant_id'):
        raise HTTPException(
            status_code=403,
            detail="User does not have tenant access"
        )
    return user

async def get_caan_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user and ensure they have CAAN_SMD role."""
    if user.get('role') not in ['CAAN_SMD', 'SUPER_ADMIN']:
        raise HTTPException(
            status_code=403,
            detail="CAAN_SMD role required"
        )
    return user

async def get_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user and ensure they have SUPER_ADMIN role."""
    if user.get('role') != 'SUPER_ADMIN':
        raise HTTPException(
            status_code=403,
            detail="SUPER_ADMIN role required"
        )
    return user