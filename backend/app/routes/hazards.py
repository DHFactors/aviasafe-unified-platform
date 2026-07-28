from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from loguru import logger

from app.models.hazard import HazardCreate, HazardUpdate, HazardResponse, HazardListItem, HazardStatus
from app.middleware.auth import get_current_user, get_tenant_user, get_safety_manager
from app.services.hazard_service import HazardService

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_hazard(
    hazard: HazardCreate,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    tenant_id = user["tenant_id"]
    service = HazardService(tenant_id)
    payload = hazard.model_dump()
    payload["tenant_id"] = tenant_id
    stored = service.create_hazard(payload, user)
    return _to_hazard_response(stored)


@router.get("/", response_model=List[HazardListItem])
async def list_hazards(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    taxonomy: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
):
    svc_user = user
    effective_tenant = user.get("tenant_id")
    if user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"] and tenant_id:
        effective_tenant = tenant_id

    service = HazardService(effective_tenant)
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if source:
        filters["source"] = source
    if taxonomy:
        filters["taxonomy"] = taxonomy
    if search:
        filters["search"] = search
    if tenant_id and user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"]:
        filters["tenant_id"] = tenant_id

    docs = service.list_hazards(svc_user, filters)
    return [_to_list_item(d) for d in docs]


@router.get("/stats", response_model=dict)
async def get_hazard_stats(
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = HazardService(user.get("tenant_id", "default"))
    stats = service.get_hazard_stats(user)
    return stats


@router.get("/{hazard_id}", response_model=dict)
async def get_hazard(
    hazard_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    effective_tenant = user.get("tenant_id", "default")
    service = HazardService(effective_tenant)
    doc = service.get_hazard_by_id(hazard_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return _to_hazard_response(doc)


@router.put("/{hazard_id}", response_model=dict)
async def update_hazard(
    hazard_id: str,
    data: HazardUpdate,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    tenant_id = user["tenant_id"]
    service = HazardService(tenant_id)
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = service.update_hazard(hazard_id, payload, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return _to_hazard_response(updated)


@router.patch("/{hazard_id}/status", response_model=dict)
async def update_hazard_status(
    hazard_id: str,
    status: HazardStatus,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    tenant_id = user["tenant_id"]
    service = HazardService(tenant_id)
    updated = service.update_status(hazard_id, status.value, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return _to_hazard_response(updated)


@router.patch("/{hazard_id}/assign", response_model=dict)
async def assign_hazard(
    hazard_id: str,
    assigned_to: str,
    assigned_to_uid: str,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    tenant_id = user["tenant_id"]
    service = HazardService(tenant_id)
    updated = service.assign_hazard(hazard_id, assigned_to, assigned_to_uid, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return _to_hazard_response(updated)


def _to_hazard_response(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "hazard_id": data.get("hazard_id", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "source": data.get("source", ""),
        "source_id": data.get("source_id"),
        "source_url": data.get("source_url"),
        "adrep_category": data.get("adrep_category"),
        "occurrence_type": data.get("occurrence_type"),
        "taxonomy": data.get("taxonomy", ""),
        "taxonomy_specific": data.get("taxonomy_specific"),
        "consequence": data.get("consequence"),
        "severity": data.get("severity"),
        "probability": data.get("probability"),
        "risk_index": data.get("risk_index"),
        "risk_level": data.get("risk_level"),
        "risk_outcome": data.get("risk_outcome"),
        "priority": data.get("priority", ""),
        "recommended_action": data.get("recommended_action"),
        "corrective_action": data.get("corrective_action"),
        "assigned_to": data.get("assigned_to"),
        "assigned_to_uid": data.get("assigned_to_uid"),
        "srm_conducted": data.get("srm_conducted", False),
        "srm_date": data.get("srm_date"),
        "srm_status": data.get("srm_status"),
        "status": data.get("status", "Open"),
        "follow_up_date": data.get("follow_up_date"),
        "closed_at": data.get("closed_at"),
        "closed_by": data.get("closed_by"),
        "tenant_id": data.get("tenant_id", ""),
        "created_by": data.get("created_by"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "remarks": data.get("remarks"),
    }


def _to_list_item(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "hazard_id": data.get("hazard_id", ""),
        "title": data.get("title", ""),
        "source": data.get("source", ""),
        "taxonomy": data.get("taxonomy", ""),
        "priority": data.get("priority", ""),
        "risk_level": data.get("risk_level"),
        "status": data.get("status", "Open"),
        "assigned_to": data.get("assigned_to"),
        "created_at": data.get("created_at"),
        "severity": data.get("severity"),
        "probability": data.get("probability"),
        "risk_index": data.get("risk_index"),
    }
