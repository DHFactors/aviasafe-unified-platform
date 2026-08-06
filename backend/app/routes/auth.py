# ============================================================================
# FILE: auth.py
# PATH: backend/app/routes/auth.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-03
# PURPOSE: Authentication endpoints with Firebase Auth integration.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.config import settings
from app.firebase import get_auth, verify_firebase_token, create_custom_claims
from app.middleware.rate_limit import rate_limit
from app.middleware.auth import resolve_user_context
from app.services.audit_service import log_audit, request_context

router = APIRouter()


class LoginRequest(BaseModel):
    id_token: str


class LoginResponse(BaseModel):
    uid: str
    email: str
    role: str
    tenant_id: Optional[str]
    custom_claims: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: str
    role: str = settings.ROLE_DEFAULT_REGISTRATION
    tenant_id: Optional[str] = None


@router.post("/verify")
@rate_limit("auth_attempts")
async def verify_token(request: Request, body: LoginRequest):
    decoded_token = verify_firebase_token(body.id_token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    role = decoded_token.get('role', settings.ROLE_DEFAULT)
    tenant_id = decoded_token.get('tenant_id')
    resolved = resolve_user_context(decoded_token.get('email', ''), role, tenant_id)
    ip, request_id = request_context(request)
    log_audit(
        action="LOGIN",
        user=decoded_token.get('email', ''),
        tenant_id=resolved["tenant_id"],
        ip=ip,
        request_id=request_id,
    )
    return {
        "uid": decoded_token['uid'],
        "email": decoded_token.get('email', ''),
        "role": resolved["role"],
        "tenant_id": resolved["tenant_id"],
    }

@router.post("/register")
async def register_user(request: RegisterRequest):
    try:
        allowed_roles = {settings.ROLE_DEFAULT_REGISTRATION}
        if request.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Registration role must be one of: {', '.join(allowed_roles)}"
            )

        auth = get_auth()
        user = auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.full_name,
            email_verified=False,
        )

        claims = {"role": request.role}
        if request.tenant_id:
            claims["tenant_id"] = request.tenant_id

        auth.set_custom_user_claims(user.uid, claims)

        ip, request_id = request_context(request)
        log_audit(
            action="REGISTER",
            user=request.email,
            tenant_id=request.tenant_id,
            ip=ip,
            request_id=request_id,
        )

        return {
            "success": True,
            "uid": user.uid,
            "email": user.email,
            "role": request.role,
            "tenant_id": request.tenant_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh Firebase ID token."""
    # Client handles token refresh using Firebase SDK
    # This endpoint just returns a success response
    return {"success": True, "message": "Token refresh handled by client"}
