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
from typing import Dict, Any

from app.core.config import settings
from app.firebase import verify_firebase_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    token = credentials.credentials
    decoded_token = verify_firebase_token(token)

    if not decoded_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = decoded_token.get('role', settings.ROLE_DEFAULT)
    tenant_id = decoded_token.get('tenant_id')

    return {
        "uid": decoded_token['uid'],
        "email": decoded_token.get('email', ''),
        "role": role,
        "tenant_id": tenant_id,
        "claims": {"role": role, "tenant_id": tenant_id}
    }


async def get_tenant_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if not user.get('tenant_id'):
        raise HTTPException(
            status_code=403,
            detail="User does not have tenant access"
        )
    return user


async def get_caan_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if user.get('role') not in settings.CROSS_TENANT_ROLES:
        raise HTTPException(
            status_code=403,
            detail="CAAN_SMD role required"
        )
    return user


async def get_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if user.get('role') not in settings.SUPER_ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="SUPER_ADMIN role required"
        )
    return user


async def get_safety_manager(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    if user.get('role') not in settings.CROSS_TENANT_ROLES and user.get('role') != "AIRLINE_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Safety Manager or CAAN_SMD role required"
        )
    if user.get('role') == "AIRLINE_ADMIN" and not user.get('tenant_id'):
        raise HTTPException(
            status_code=403,
            detail="Tenant access required for AIRLINE_ADMIN"
        )
    return user