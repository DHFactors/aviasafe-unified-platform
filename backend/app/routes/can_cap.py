from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from loguru import logger
from datetime import datetime, timezone

from app.models.can_cap import (
    CANCreate, CANUpdate, CANResponse, CANListItem,
    CAPCreate, CAPUpdate, CAPReview, CAPResponse, CANStatus, CAPStatus
)
from app.middleware.auth import get_current_user, get_tenant_user, get_safety_manager, get_responsible_manager
from app.services.can_cap_service import CanCapService

router = APIRouter()


# ─── CAN Endpoints ───

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def issue_can(
    can: CANCreate,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    stored = service.issue_can(can.model_dump(), user)
    return _to_can_response(stored)


@router.get("/", response_model=List[CANListItem])
async def list_cans(
    hazard_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
):
    effective_tenant = user.get("tenant_id", "default")
    service = CanCapService(effective_tenant)
    filters = {}
    if hazard_id:
        filters["hazard_id"] = hazard_id
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if search:
        filters["search"] = search

    docs = service.list_cans(user, filters)
    return [_to_can_list_item(d) for d in docs]


@router.get("/stats", response_model=dict)
async def get_can_stats(
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = CanCapService(user.get("tenant_id", "default"))
    can_stats = service.get_can_stats(user)
    cap_stats = service.get_cap_stats(user)
    return {"cans": can_stats, "caps": cap_stats}


@router.get("/{can_id}", response_model=dict)
async def get_can(
    can_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    effective_tenant = user.get("tenant_id", "default")
    service = CanCapService(effective_tenant)
    doc = service.get_can(can_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="CAN not found")
    return _to_can_response(doc)


@router.patch("/{can_id}/status", response_model=dict)
async def update_can_status(
    can_id: str,
    status: CANStatus,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    updated = service.update_can_status(can_id, status.value, user)
    if not updated:
        raise HTTPException(status_code=404, detail="CAN not found")
    return _to_can_response(updated)


@router.delete("/{can_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_can(
    can_id: str,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    deleted = service.delete_can(can_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="CAN not found")


# ─── CAP Endpoints ───

@router.post("/{can_id}/caps", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_cap(
    can_id: str,
    cap: CAPCreate,
    user: Dict[str, Any] = Depends(get_responsible_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    try:
        stored = service.submit_cap(cap.can_id, cap.model_dump(), user)
        return _to_cap_response(stored)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{can_id}/caps", response_model=List[CAPResponse])
async def list_caps(
    can_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    effective_tenant = user.get("tenant_id", "default")
    service = CanCapService(effective_tenant)
    docs = service.list_caps(can_id, user)
    return [_to_cap_list_item(d) for d in docs]


@router.get("/caps/{cap_id}", response_model=dict)
async def get_cap(
    cap_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    effective_tenant = user.get("tenant_id", "default")
    service = CanCapService(effective_tenant)
    doc = service.get_cap(cap_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="CAP not found")
    return _to_cap_response(doc)


@router.patch("/caps/{cap_id}", response_model=dict)
async def update_cap(
    cap_id: str,
    data: CAPUpdate,
    user: Dict[str, Any] = Depends(get_responsible_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = service.update_cap(cap_id, payload, user)
    if not updated:
        raise HTTPException(status_code=404, detail="CAP not found")
    return _to_cap_response(updated)


@router.patch("/caps/{cap_id}/review", response_model=dict)
async def review_cap(
    cap_id: str,
    review: CAPReview,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    updated = service.review_cap(cap_id, review.model_dump(), user)
    if not updated:
        raise HTTPException(status_code=404, detail="CAP not found")
    return _to_cap_response(updated)


@router.patch("/caps/{cap_id}/status", response_model=dict)
async def update_cap_status(
    cap_id: str,
    status: CAPStatus,
    user: Dict[str, Any] = Depends(get_responsible_manager),
):
    tenant_id = user["tenant_id"]
    service = CanCapService(tenant_id)
    updated = service.update_cap(cap_id, {"status": status.value}, user)
    if not updated:
        raise HTTPException(status_code=404, detail="CAP not found")
    return _to_cap_response(updated)


# ─── Response Helpers ───

def _to_can_response(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "can_reference": data.get("can_reference", ""),
        "hazard_id": data.get("hazard_id", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "required_action": data.get("required_action", ""),
        "issued_by": data.get("issued_by", ""),
        "issued_by_uid": data.get("issued_by_uid", ""),
        "issued_at": data.get("issued_at"),
        "target_completion_date": data.get("target_completion_date"),
        "assigned_to": data.get("assigned_to", ""),
        "assigned_to_uid": data.get("assigned_to_uid", ""),
        "priority": data.get("priority", ""),
        "status": data.get("status", "Open"),
        "tenant_id": data.get("tenant_id", ""),
        "created_by": data.get("created_by"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "latest_cap": data.get("latest_cap"),
    }


def _to_can_list_item(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "can_reference": data.get("can_reference", ""),
        "hazard_id": data.get("hazard_id", ""),
        "title": data.get("title", ""),
        "priority": data.get("priority", ""),
        "status": data.get("status", "Open"),
        "assigned_to": data.get("assigned_to", ""),
        "target_completion_date": data.get("target_completion_date"),
        "issued_at": data.get("issued_at"),
    }


def _to_cap_response(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "can_id": data.get("can_id", ""),
        "cap_reference": data.get("cap_reference", ""),
        "action_plan": data.get("action_plan", ""),
        "timeline": data.get("timeline", ""),
        "resources_required": data.get("resources_required"),
        "implementation_plan": data.get("implementation_plan"),
        "submitted_by": data.get("submitted_by", ""),
        "submitted_by_uid": data.get("submitted_by_uid", ""),
        "submitted_at": data.get("submitted_at"),
        "target_completion_date": data.get("target_completion_date"),
        "status": data.get("status", "In Progress"),
        "reviewed_by": data.get("reviewed_by"),
        "reviewed_by_uid": data.get("reviewed_by_uid"),
        "reviewed_at": data.get("reviewed_at"),
        "review_comments": data.get("review_comments"),
        "revision_deadline": data.get("revision_deadline"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def _to_cap_list_item(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "can_id": data.get("can_id", ""),
        "cap_reference": data.get("cap_reference", ""),
        "status": data.get("status", "In Progress"),
        "submitted_by": data.get("submitted_by", ""),
        "submitted_at": data.get("submitted_at"),
    }
