# ============================================================================
# FILE: state_risk.py
# PATH: backend/app/routes/state_risk.py
# VERSION: 1.0.0
# DATE CREATED: 2026-08-04
# PURPOSE: State-level risk register endpoints. CAAN_SMD / SUPER_ADMIN view the
#          national risk profile (aggregated across tenants, measured against
#          SSP targets). SUPER_ADMIN maintains SSP targets.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from loguru import logger

from app.middleware.auth import get_caan_user, get_admin_user
from app.services.state_risk_service import StateRiskService

router = APIRouter()


class SspTargetUpdate(BaseModel):
    ssp_target: float = Field(..., description="SSP target for this risk category (1-25 risk index)")
    risk_reduction_rate: Optional[float] = Field(None, description="Targeted annual risk reduction %")


@router.get("/register")
async def get_state_risk_register(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    """Return the state-level risk register, optionally filtered by period."""
    svc = StateRiskService(user)
    rows = svc.list_register(year=year, quarter=quarter)
    return {"success": True, "count": len(rows), "risks": rows}


@router.get("/aggregate")
async def get_aggregated_national_risk(
    year: int = Query(..., ge=2000, le=2100),
    quarter: int = Query(..., ge=1, le=4),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    """Aggregate risk across all tenants by ICAO category (live computation,
    not yet persisted)."""
    svc = StateRiskService(user)
    return {"success": True, **svc.aggregate_national_risk(year, quarter)}


@router.post("/sync")
async def sync_state_risk_register(
    year: int = Query(..., ge=2000, le=2100),
    quarter: int = Query(..., ge=1, le=4),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    """Persist the aggregated national risk into the state risk register,
    carrying over existing SSP targets where present."""
    svc = StateRiskService(user)
    result = svc.sync_register_from_aggregation(year, quarter)
    logger.info(f"State risk register synced for {year}Q{quarter} by {user.get('uid')}")
    return {"success": True, **result}


@router.put("/register/{risk_id}/ssp-target")
async def update_ssp_target(
    risk_id: str,
    body: SspTargetUpdate,
    user: Dict[str, Any] = Depends(get_admin_user),
):
    """Set the SSP target for a risk category (SUPER_ADMIN only)."""
    svc = StateRiskService(user)
    updated = svc.update_ssp_target(risk_id, body.ssp_target, body.risk_reduction_rate)
    if not updated:
        raise HTTPException(status_code=404, detail="Risk register entry not found")
    logger.info(f"SSP target updated for {risk_id} by {user.get('uid')}")
    return {"success": True, "risk": updated}
