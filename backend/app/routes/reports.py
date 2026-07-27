# ============================================================================
# FILE: reports.py
# PATH: backend/app/routes/reports.py
# VERSION: 2.1.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-27
# PURPOSE: API endpoints for safety report submission and retrieval.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.report import ReportCreate, ReportResponse, ReportListItem
from app.middleware.auth import get_tenant_user, get_safety_manager
from app.services.report_service import ReportService
from app.services.risk_matrix import compute_risk_index, get_risk_level

router = APIRouter()


class RiskAssessmentRequest(BaseModel):
    severity: int = Field(..., ge=1, le=5, description="1-5 ICAO severity")
    probability: int = Field(..., ge=1, le=5, description="1-5 ICAO probability")
    notes: Optional[str] = None


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    report: ReportCreate,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    """Submit a new safety report.

    Flow:
      1. Validate request body (Pydantic)
      2. Authenticate via JWT (middleware)
      3. Persist to Firestore with tenant isolation
      4. Return HTTP 201 immediately
      5. AI classification runs as a background task

    The client receives the response before AI processing completes.
    Poll GET /api/reports/{id} to check ai_status.
    """
    tenant_id = user["tenant_id"]
    service = ReportService(tenant_id)

    stored = service.create_report(report.model_dump(), user)

    # Schedule AI analysis after response is sent
    background_tasks.add_task(service.run_ai_analysis, stored["id"], report.narrative)

    return _to_report_response(stored)


@router.get("/", response_model=List[ReportListItem])
async def get_reports(
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    """Retrieve safety reports for the authenticated user's tenant.

    AIRLINE_ADMIN: reports scoped to their tenant.
    CAAN_SMD / SUPER_ADMIN: cross-tenant view.
    """
    tenant_id = user["tenant_id"]
    service = ReportService(tenant_id)

    docs = service.get_reports(user)
    return [_to_list_item(d) for d in docs]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    """Retrieve a single safety report by ID."""
    tenant_id = user["tenant_id"]
    service = ReportService(tenant_id)

    doc = service.get_report_by_id(report_id, user)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    return _to_report_response(doc)


@router.put("/{report_id}/risk-assessment", response_model=ReportResponse)
async def confirm_risk_assessment(
    report_id: str,
    assessment: RiskAssessmentRequest,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    """Safety Manager confirms the official ICAO risk assessment for a report.

    Severity x Probability = Risk Index determines Risk Level.
    AIRLINE_ADMIN: scoped to their tenant.
    CAAN_SMD / SUPER_ADMIN: cross-tenant access.
    """
    tenant_id = user["tenant_id"]
    service = ReportService(tenant_id)

    updated = service.confirm_risk_assessment(
        report_id=report_id,
        severity=assessment.severity,
        probability=assessment.probability,
        user=user,
        notes=assessment.notes,
    )

    return _to_report_response(updated)


def _to_report_response(data: dict) -> dict:
    """Transform stored Firestore document into ReportResponse shape."""
    return {
        "id": data.get("id", ""),
        "tenant_id": data.get("tenant_id", ""),
        "report_type": data.get("report_type", "voluntary"),
        "status": data.get("status", "NEW"),
        "ai_status": data.get("ai_status", "PENDING"),
        "narrative": data.get("narrative", ""),
        "location": data.get("location", ""),
        "occurrence_date": data.get("occurrence_date"),
        "created_by": data.get("created_by", ""),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "is_anonymous": data.get("is_anonymous", False),
        "flight_number": data.get("flight_number"),
        "aircraft_registration": data.get("aircraft_registration"),
        "occurrence_type": data.get("occurrence_type"),
        "severity": data.get("severity"),
        "attachments": data.get("attachments"),
        "risk_score": data.get("risk_score"),
        "likelihood": data.get("likelihood"),
        "consequence": data.get("consequence"),
        "bowtie_hazard": data.get("bowtie_hazard"),
        "bowtie_barrier": data.get("bowtie_barrier"),
        "sms_category": data.get("sms_category"),
        "investigation_status": data.get("investigation_status"),
        "corrective_actions": data.get("corrective_actions"),
        "lessons_learned": data.get("lessons_learned"),
        "safety_action_required": data.get("safety_action_required", False),
        "reviewed_by": data.get("reviewed_by"),
        "reviewed_at": data.get("reviewed_at"),
        "ai_analysis": data.get("ai_analysis"),
        "severity_level": data.get("severity_level"),
        "probability_level": data.get("probability_level"),
        "risk_index": data.get("risk_index"),
        "risk_level": data.get("risk_level"),
        "risk_assessment": data.get("risk_assessment"),
        "ai_suggested_assessment": data.get("ai_suggested_assessment"),
    }


def _to_list_item(data: dict) -> dict:
    """Transform stored document into ReportListItem shape."""
    return {
        "id": data.get("id", ""),
        "tenant_id": data.get("tenant_id", ""),
        "report_type": data.get("report_type", "voluntary"),
        "status": data.get("status", "NEW"),
        "ai_status": data.get("ai_status", "PENDING"),
        "location": data.get("location", ""),
        "occurrence_date": data.get("occurrence_date"),
        "created_by": data.get("created_by", ""),
        "created_at": data.get("created_at"),
        "is_anonymous": data.get("is_anonymous", False),
        "occurrence_type": data.get("occurrence_type"),
        "severity": data.get("severity"),
        "risk_score": data.get("risk_score"),
        "risk_level": data.get("risk_level"),
        "severity_level": data.get("severity_level"),
        "probability_level": data.get("probability_level"),
    }
