from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from loguru import logger

from app.models.verification import VerificationCreate, VerificationResponse, ClosureCreate, ClosureResponse, VerificationStats
from app.middleware.auth import get_current_user, get_tenant_user, get_safety_manager, get_accountable_executive
from app.services.verification_service import VerificationService
from app.services.hazard_service import HazardService

router = APIRouter()


def _get_service(user: dict) -> VerificationService:
    tenant_id = user.get("tenant_id", "default")
    return VerificationService(tenant_id)


# ── Verification Endpoints ──


@router.post("/hazards/{hazard_id}/verifications", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_verification(
    hazard_id: str,
    verification: VerificationCreate,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    if not user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant access required")
    service = _get_service(user)
    try:
        stored = service.create_verification(hazard_id, verification.model_dump(), user)
        return _to_verification_response(stored)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hazards/{hazard_id}/verifications", response_model=List[dict])
async def list_verifications(
    hazard_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = _get_service(user)
    docs = service.list_verifications(hazard_id, user)
    return [_to_verification_response(d) for d in docs]


@router.get("/verifications/stats", response_model=VerificationStats)
async def get_verification_stats(
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = _get_service(user)
    stats = service.get_verification_stats(user)
    return stats


@router.get("/verifications/{verification_id}", response_model=dict)
async def get_verification(
    verification_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = _get_service(user)
    doc = service.get_verification(verification_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _to_verification_response(doc)


# ── Closure Endpoints ──


@router.post("/hazards/{hazard_id}/closure", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_closure(
    hazard_id: str,
    closure: ClosureCreate,
    user: Dict[str, Any] = Depends(get_accountable_executive),
):
    if not user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant access required")
    service = _get_service(user)
    try:
        stored = service.create_closure(hazard_id, closure.model_dump(), user)
        return _to_closure_response(stored)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hazards/{hazard_id}/closure", response_model=dict)
async def get_closure(
    hazard_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = _get_service(user)
    doc = service.get_closure(hazard_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="Closure not found")
    return _to_closure_response(doc)


# ── Reopen Endpoint ──


@router.patch("/hazards/{hazard_id}/reopen", response_model=dict)
async def reopen_hazard(
    hazard_id: str,
    reason: str = Query(..., min_length=5),
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    if not user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant access required")
    tenant_id = user.get("tenant_id", "default")
    service = VerificationService(tenant_id)
    updated = service.reopen_hazard(hazard_id, reason, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return _to_reopen_response(updated, reason)


# ── Response Helpers ──


def _to_verification_response(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "hazard_id": data.get("hazard_id", ""),
        "cap_id": data.get("cap_id", ""),
        "outcome": data.get("outcome", ""),
        "comments": data.get("comments"),
        "evidence": data.get("evidence", []),
        "verified_by": data.get("verified_by", ""),
        "verified_by_uid": data.get("verified_by_uid", ""),
        "verification_date": data.get("verification_date"),
        "revision_deadline": data.get("revision_deadline"),
        "revision_notes": data.get("revision_notes"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def _to_closure_response(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "hazard_id": data.get("hazard_id", ""),
        "lessons_learned": data.get("lessons_learned"),
        "recommendations": data.get("recommendations"),
        "approval_notes": data.get("approval_notes"),
        "approved_by": data.get("approved_by", ""),
        "approved_by_uid": data.get("approved_by_uid", ""),
        "approved_at": data.get("approved_at"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def _to_reopen_response(data: dict, reason: str) -> dict:
    return {
        "hazard_id": data.get("hazard_id", data.get("id", "")),
        "status": data.get("status", "Reopened"),
        "reopen_reason": reason,
        "reopened_at": data.get("updated_at"),
    }
