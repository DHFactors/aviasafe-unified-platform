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
from app.firebase import get_auth, verify_firebase_token, create_custom_claims

router = APIRouter()

class LoginRequest(BaseModel):
    """Login request model."""
    id_token: str  # Firebase ID token from client

class LoginResponse(BaseModel):
    """Login response model."""
    uid: str
    email: str
    role: str
    tenant_id: Optional[str]
    custom_claims: dict

class RegisterRequest(BaseModel):
    """Registration request model."""
    email: EmailStr
    password: str
    full_name: str
    organization: str
    role: str = "AIRLINE_ADMIN"
    tenant_id: Optional[str] = None

@router.post("/verify", response_model=LoginResponse)
async def verify_token(request: LoginRequest):
    """Verify Firebase ID token and return user info."""
    # Verify the token
    decoded_token = verify_firebase_token(request.id_token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get custom claims
    custom_claims = decoded_token.get('claims', {})
    
    return LoginResponse(
        uid=decoded_token['uid'],
        email=decoded_token.get('email', ''),
        role=custom_claims.get('role', 'USER'),
        tenant_id=custom_claims.get('tenant_id'),
        custom_claims=custom_claims
    )

@router.post("/register")
async def register_user(request: RegisterRequest):
    """Create a new user in Firebase Auth with custom claims."""
    try:
        # Create user in Firebase Auth
        auth = get_auth()
        user = auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.full_name,
            email_verified=False
        )
        
        # Set custom claims (role and tenant)
        claims = {"role": request.role}
        if request.tenant_id:
            claims["tenant_id"] = request.tenant_id
        
        auth.set_custom_user_claims(user.uid, claims)
        
        return {
            "success": True,
            "uid": user.uid,
            "email": user.email,
            "role": request.role,
            "tenant_id": request.tenant_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh Firebase ID token."""
    # Client handles token refresh using Firebase SDK
    # This endpoint just returns a success response
    return {"success": True, "message": "Token refresh handled by client"}
