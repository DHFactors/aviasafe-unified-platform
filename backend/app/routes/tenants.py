# ============================================================================
# FILE: tenants.py
# PATH: backend/app/routes/tenants.py
# PURPOSE: Per-tenant configuration endpoints. Phase 1 exposes the survey rate
#          limit control (tenants/{tid}/config). Phase 3 extends the same PUT
#          contract with survey instructions and adds an auth-optional GET.
# ============================================================================

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import settings
from app.firebase import get_db
from app.middleware.auth import get_current_user
from app.services.audit_service import log_audit, request_context

router = APIRouter()

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
