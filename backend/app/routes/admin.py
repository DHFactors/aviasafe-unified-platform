# ============================================================================
# FILE: admin.py
# PATH: backend/app/routes/admin.py
# VERSION: 2.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-27
# PURPOSE: Admin and Safety Manager endpoints for system configuration.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime, timezone

from app.middleware.auth import get_safety_manager, get_admin_user
from app.services.risk_matrix import (
    get_risk_matrix_config,
    set_risk_matrix_config,
    THRESHOLDS_DEFAULT,
)

router = APIRouter()


class RiskMatrixThresholds(BaseModel):
    low_max: int = Field(default=5, ge=1, le=25)
    medium_max: int = Field(default=9, ge=1, le=25)
    high_max: int = Field(default=15, ge=1, le=25)


class RiskMatrixConfig(BaseModel):
    thresholds: RiskMatrixThresholds
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/risk-matrix")
async def get_risk_matrix(
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    """Get the ICAO risk matrix configuration for the user's tenant.

    Defaults to ICAO-aligned thresholds if not yet configured.
    """
    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"]:
        tenant_id = "default"
    config = get_risk_matrix_config(tenant_id)
    return config


@router.put("/risk-matrix", status_code=status.HTTP_200_OK)
async def update_risk_matrix(
    config: RiskMatrixConfig,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    """Update the ICAO risk matrix thresholds for the user's tenant.

    Thresholds define Low/Medium/High/Very High boundaries.
    All thresholds are inclusive max values for each level.
    Must satisfy: 1 <= low_max < medium_max < high_max <= 25.
    """
    t = config.thresholds
    if not (1 <= t.low_max < t.medium_max < t.high_max <= 25):
        raise HTTPException(
            status_code=400,
            detail="Thresholds must satisfy: 1 <= low_max < medium_max < high_max <= 25",
        )

    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"]:
        tenant_id = "default"

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "thresholds": t.model_dump(),
        "updated_by": user["uid"],
        "updated_at": now,
    }
    set_risk_matrix_config(tenant_id, data)
    logger.info(f"Risk matrix updated for tenant {tenant_id} by {user['uid']}")
    return data
