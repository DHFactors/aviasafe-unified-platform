# ============================================================================
# FILE: tenants.py
# PATH: backend/app/routes/tenants.py
# PURPOSE: Per-tenant configuration endpoints. Phase 1 exposes the survey rate
#          limit control (tenants/{tid}/config). Phase 3 extends the same PUT
#          contract with survey instructions and adds an auth-optional GET.
# ============================================================================

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import settings
from app.firebase import get_db
from app.middleware.auth import get_current_user
from app.services.audit_service import log_audit, request_context
from app.services.users import list_tenant_users

router = APIRouter()

optional_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> Optional[Dict[str, Any]]:
    """Return the authenticated user when a Bearer token is supplied.

    Public pages (e.g. the survey) must be able to read tenant config without
    a login. A supplied but invalid token is still rejected with 401.
    """
    if credentials is None:
        return None
    return await get_current_user(credentials)

SURVEY_RATE_LIMIT_OPTIONS = (5, 10, 25, 50, 100)


def _envelope(data: Any) -> Dict[str, Any]:
    return {
        "status": "success",
        "timestamp": datetime.now(),
        "data": data,
    }


class TenantConfigUpdate(BaseModel):
    survey_rate_limit: int = Field(..., description="Max daily survey submissions for this tenant")
    survey_instructions: str = Field(None, description="Optional instructions shown at the top of the survey")


def _require_tenant_admin(user: Dict[str, Any], tenant_id: str) -> None:
    """Phase 1: only the AIRLINE_ADMIN of the target tenant may edit its config."""
    if user.get("role") != "AIRLINE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the AIRLINE_ADMIN of this tenant can update its config",
        )
    if user.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenantId does not match the authenticated user's tenant",
        )


def _require_tenant_viewer(user: Dict[str, Any], tenant_id: str) -> None:
    """Phase 2: AIRLINE_ADMIN of the tenant or SUPER_ADMIN may list users."""
    if user.get("role") == "SUPER_ADMIN":
        return
    if user.get("role") != "AIRLINE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the AIRLINE_ADMIN of this tenant or SUPER_ADMIN can view users",
        )
    if user.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenantId does not match the authenticated user's tenant",
        )


@router.get("/{tenant_id}/config", status_code=status.HTTP_200_OK)
async def get_tenant_config(
    tenant_id: str,
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    """Read per-tenant configuration (survey rate limit, survey instructions).

    Authentication is optional: the public survey page calls this to render the
    airline's instructions at the top of the survey. Returns 404 for unknown
    tenants. The config map is returned as stored (missing fields omitted).
    """
    tenant_id = tenant_id.strip()
    db = get_db()
    tenant_ref = db.collection(settings.FIREBASE_COLLECTION_TENANTS).document(tenant_id)
    try:
        tenant_snap = tenant_ref.get()
    except Exception as e:
        logger.warning(f"Tenant config lookup failed for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Tenant storage unavailable")
    if not tenant_snap.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown tenant: {tenant_id}")

    tenant_data = tenant_snap.to_dict() or {}
    config = tenant_data.get("config") or {}
    return _envelope({
        "tenant_id": tenant_id,
        "name": tenant_data.get("name"),
        "config": config,
    })


@router.get("/{tenant_id}/users", status_code=status.HTTP_200_OK)
async def list_users(
    tenant_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List the authorized users for a tenant (view-only).

    AIRLINE_ADMIN of the target tenant or SUPER_ADMIN. Returns uid, email, role,
    createdAt and lastLogin (when available) from the mirrored users collection.
    """
    tenant_id = tenant_id.strip()
    _require_tenant_viewer(user, tenant_id)
    try:
        users = list_tenant_users(tenant_id)
    except Exception as e:
        logger.warning(f"Failed to list users for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenant users")
    return _envelope({"tenant_id": tenant_id, "users": users})


@router.put("/{tenant_id}/config", status_code=status.HTTP_200_OK)
async def update_tenant_config(
    tenant_id: str,
    config: TenantConfigUpdate,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Update per-tenant configuration (survey rate limit, survey instructions).

    AIRLINE_ADMIN of the target tenant only. The survey_rate_limit must be one
    of the operator-selectable options (5, 10, 25, 50, 100).
    """
    tenant_id = tenant_id.strip()
    if config.survey_rate_limit not in SURVEY_RATE_LIMIT_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"survey_rate_limit must be one of {', '.join(str(o) for o in SURVEY_RATE_LIMIT_OPTIONS)}",
        )

    _require_tenant_admin(user, tenant_id)

    db = get_db()
    tenant_ref = db.collection(settings.FIREBASE_COLLECTION_TENANTS).document(tenant_id)
    try:
        tenant_snap = tenant_ref.get()
    except Exception as e:
        logger.warning(f"Tenant config lookup failed for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Tenant storage unavailable")
    if not tenant_snap.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown tenant: {tenant_id}")

    existing = (tenant_snap.to_dict() or {}).get("config") or {}
    updated = dict(existing)
    updated["survey_rate_limit"] = config.survey_rate_limit
    if config.survey_instructions is not None:
        updated["survey_instructions"] = config.survey_instructions

    now = datetime.now()
    try:
        tenant_ref.update({"config": updated})
    except Exception as e:
        logger.error(f"Failed to persist config for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist tenant config")

    ip, request_id = request_context(request)
    log_audit(
        action="TENANT_CONFIG_UPDATED",
        user=user.get("email") or user.get("uid"),
        tenant_id=tenant_id,
        target_type="tenant",
        target_id=tenant_id,
        ip=ip,
        request_id=request_id,
        metadata={"survey_rate_limit": config.survey_rate_limit},
    )

    return _envelope({"tenant_id": tenant_id, "config": updated})
