# ============================================================================
# FILE: dashboard.py
# PATH: backend/app/routes/dashboard.py
# VERSION: 2.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-27
# PURPOSE: Thin route controllers for dashboard analytics.
#          No business logic — delegates entirely to DashboardService.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from datetime import datetime

from app.middleware.auth import get_current_user, get_tenant_user, get_caan_user, get_admin_user
from app.services.dashboard_service import DashboardService
from loguru import logger

router = APIRouter()


def _envelope(data: Any) -> Dict[str, Any]:
    return {
        "status": "success",
        "timestamp": datetime.now(),
        "data": data,
    }


def _empty_kpis():
    return {
        "total_reports": 0, "open_reports": 0, "closed_reports": 0,
        "high_risk_reports": 0, "critical_reports": 0,
        "anonymous_percentage": 0.0, "avg_closure_days": None,
        "reporting_rate_trend": None, "repeat_occurrence_rate": None,
    }


def _empty_ai_kpis():
    return {
        "ai_processed": 0, "ai_pending": 0, "ai_failed": 0,
        "avg_processing_time_ms": None, "avg_confidence": None,
        "model_versions": {},
    }


def _empty_org_kpis():
    return {
        "active_reporters": 0, "reporting_frequency": None,
        "corrective_actions_open": 0, "corrective_actions_closed": 0,
        "safety_actions_overdue": 0, "investigation_backlog": 0,
    }


# ======================================================================
# Airline Dashboard (tenant-scoped)
# ======================================================================


@router.get("/overview")
async def get_dashboard_overview(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    svc = DashboardService(user)
    try:
        data = svc.get_airline_overview(days=days)
        return _envelope(data)
    except Exception as e:
        logger.error(f"Dashboard overview failed for tenant {user.get('tenant_id')}: {e}")
        return _envelope({
            "kpis": _empty_kpis(),
            "ai_kpis": _empty_ai_kpis(),
            "org_kpis": _empty_org_kpis(),
        })


def _safe_airline(method_name: str, svc: DashboardService, **kwargs) -> dict:
    try:
        fn = getattr(svc, method_name)
        return fn(**kwargs)
    except Exception as e:
        logger.error(f"{method_name} failed for tenant {svc.tenant_id}: {e}")
        return {}


@router.get("/recent")
async def get_recent_reports(
    days: int = Query(90, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    clamped = min(page_size, settings.REPO_MAX_PAGE_SIZE)
    if clamped != page_size:
        logger.info(f"page_size clamped from {page_size} to {clamped} for tenant {user.get('tenant_id')}")
    svc = DashboardService(user)
    data = _safe_airline("get_recent_reports", svc, days=days, page=page, page_size=clamped, cursor=cursor)
    return _envelope(data)


@router.get("/risk")
async def get_risk_distribution(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    svc = DashboardService(user)
    data = _safe_airline("get_risk_distribution", svc, days=days)
    return _envelope(data)


@router.get("/trends")
async def get_monthly_trends(
    days: int = Query(180, ge=1, le=730),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    svc = DashboardService(user)
    data = _safe_airline("get_monthly_trends", svc, days=days)
    return _envelope(data)


@router.get("/hazards")
async def get_hazard_frequency(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    svc = DashboardService(user)
    data = _safe_airline("get_hazard_frequency", svc, days=days)
    return _envelope(data)


@router.get("/actions")
async def get_actions_summary(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_tenant_user),
):
    svc = DashboardService(user)
    data = _safe_airline("get_actions_summary", svc, days=days)
    return _envelope(data)


# ======================================================================
# CAAN Dashboard (cross-tenant, aggregated)
# ======================================================================


@router.get("/caan/overview")
async def get_caan_overview(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    svc = DashboardService(user)
    data = svc.get_caan_overview(days=days)
    return _envelope(data)


@router.get("/caan/trends")
async def get_caan_trends(
    days: int = Query(180, ge=1, le=730),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    svc = DashboardService(user)
    data = svc.get_caan_trends(days=days)
    return _envelope(data)


@router.get("/caan/risk")
async def get_caan_risk(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    svc = DashboardService(user)
    data = svc.get_caan_risk(days=days)
    return _envelope(data)


@router.get("/caan/hazards")
async def get_caan_hazards(
    days: int = Query(90, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    svc = DashboardService(user)
    data = svc.get_caan_hazards(days=days)
    return _envelope(data)


@router.get("/caan/benchmark")
async def get_caan_benchmark(
    days: int = Query(180, ge=1, le=730),
    user: Dict[str, Any] = Depends(get_caan_user),
):
    svc = DashboardService(user)
    data = svc.get_caan_benchmark(days=days)
    return _envelope(data)


# ======================================================================
# Super Admin Dashboard (system-level)
# ======================================================================


@router.get("/admin/system")
async def get_admin_system(
    user: Dict[str, Any] = Depends(get_admin_user),
):
    svc = DashboardService(user)
    data = svc.get_admin_system()
    return _envelope(data)


@router.get("/admin/tenants")
async def get_admin_tenants(
    user: Dict[str, Any] = Depends(get_admin_user),
):
    svc = DashboardService(user)
    data = svc.get_admin_tenants()
    return _envelope(data)


@router.get("/admin/usage")
async def get_admin_usage(
    days: int = Query(30, ge=1, le=365),
    user: Dict[str, Any] = Depends(get_admin_user),
):
    svc = DashboardService(user)
    data = svc.get_admin_usage(days=days)
    return _envelope(data)
