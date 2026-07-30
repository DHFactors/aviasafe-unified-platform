# ============================================================================
# FILE: dashboard_service.py
# PATH: backend/app/services/dashboard_service.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-27
# PURPOSE: Role-aware dashboard orchestration layer.
#          Coordinates Repository and MetricsService.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.config import settings
from app.services.repository import ReportRepository, ReportFilter
from app.services.metrics_service import MetricsService


class DashboardService:
    """Orchestrates dashboard data for all roles.

    Every public method:
      1. Determines the correct filter (tenant-isolated or cross-tenant)
      2. Queries the repository
      3. Delegates calculations to MetricsService
      4. Returns a dict ready for JSON response

    Route files import only this service — never the repository or metrics directly.
    """

    DEFAULT_DAYS = settings.DASHBOARD_DEFAULT_DAYS

    def __init__(self, user: dict):
        self.user = user
        self.role = user.get("role", "USER")
        self.tenant_id = user.get("tenant_id")
        self.repo = ReportRepository()

    # ------------------------------------------------------------------
    # Public: Airline dashboard endpoints
    # ------------------------------------------------------------------

    def get_airline_overview(self, **overrides) -> Dict[str, Any]:
        f = self._base_filter(**overrides)
        reports = self.repo.get_all_in_range(f)
        kpis = MetricsService.calculate_kpis(reports)
        ai_kpis = MetricsService.calculate_ai_kpis(reports)
        org_kpis = MetricsService.calculate_org_kpis(reports)
        return {
            "kpis": kpis,
            "ai_kpis": ai_kpis,
            "org_kpis": org_kpis,
        }

    def get_recent_reports(self, **overrides) -> Dict[str, Any]:
        page_size = overrides.pop("page_size", 10) if "page_size" in overrides else 10
        cursor = overrides.pop("cursor", None) if "cursor" in overrides else None
        f = self._base_filter(**overrides).clone(page_size=page_size, cursor=cursor)
        return self.repo.query_reports(f)

    def get_risk_distribution(self, **overrides) -> List[Dict[str, Any]]:
        f = self._base_filter(**overrides)
        reports = self.repo.get_all_in_range(f)
        return MetricsService.calculate_risk_distribution(reports)

    def get_monthly_trends(self, **overrides) -> List[Dict[str, Any]]:
        f = self._base_filter(**overrides)
        reports = self.repo.get_all_in_range(f)
        return MetricsService.calculate_monthly_trends(reports)

    def get_hazard_frequency(self, **overrides) -> List[Dict[str, Any]]:
        f = self._base_filter(**overrides)
        reports = self.repo.get_all_in_range(f)
        return MetricsService.calculate_hazard_frequency(reports)

    def get_actions_summary(self, **overrides) -> Dict[str, Any]:
        f = self._base_filter(**overrides)
        reports = self.repo.get_all_in_range(f)
        return MetricsService.calculate_org_kpis(reports)

    # ------------------------------------------------------------------
    # Public: CAAN dashboard endpoints (cross-tenant, aggregated)
    # ------------------------------------------------------------------

    def _caan_reports(self, **overrides) -> list:
        try:
            f = self._caan_filter(**overrides)
            return self.repo.get_all_in_range(f)
        except Exception as e:
            logger.warning(f'CAAN dashboard query failed (missing index?): {e}')
            return []

    def get_caan_overview(self, **overrides) -> Dict[str, Any]:
        reports = self._caan_reports(**overrides)
        kpis = MetricsService.calculate_kpis(reports)
        ai_kpis = MetricsService.calculate_ai_kpis(reports)
        org_kpis = MetricsService.calculate_org_kpis(reports)

        tenant_counts = self._tenant_report_counts(reports)
        return {
            "kpis": kpis,
            "ai_kpis": ai_kpis,
            "org_kpis": org_kpis,
            "tenant_breakdown": tenant_counts,
        }

    def get_caan_trends(self, **overrides) -> Dict[str, Any]:
        reports = self._caan_reports(**overrides)
        trends = MetricsService.calculate_monthly_trends(reports)

        return {
            "monthly_trends": trends,
            "industry_avg": None,
            "prediction": None,
        }

    def get_caan_risk(self, **overrides) -> Dict[str, Any]:
        reports = self._caan_reports(**overrides)
        dist = MetricsService.calculate_risk_distribution(reports)

        tenant_severity = self._tenant_severity_breakdown(reports)
        return {
            "risk_distribution": dist,
            "tenant_severity": tenant_severity,
        }

    def get_caan_hazards(self, **overrides) -> List[Dict[str, Any]]:
        reports = self._caan_reports(**overrides)
        return MetricsService.calculate_hazard_frequency(reports)

    def get_caan_benchmark(self, **overrides) -> Dict[str, Any]:
        reports = self._caan_reports(**overrides)
        anon_count = sum(1 for r in reports if r.get("is_anonymous"))
        total = len(reports) or 1
        return {
            "anonymous_reporting_rate": round(anon_count / total * 100, 1),
            "industry_anon_rate": None,
            "anonymous_trend": None,
            "total_reporters": len(set(r.get("created_by") for r in reports if r.get("created_by"))),
            "benchmark_data": None,
        }

    # ------------------------------------------------------------------
    # Public: Super Admin dashboard endpoints
    # ------------------------------------------------------------------

    def get_admin_system(self) -> Dict[str, Any]:
        f = self._caan_filter(days=settings.DASHBOARD_ADMIN_SYSTEM_DAYS)
        weekly = self.repo.get_all_in_range(f)
        f30 = self._caan_filter(days=settings.DASHBOARD_ADMIN_TENANT_DAYS)
        monthly = self.repo.get_all_in_range(f30)

        from app.firebase import is_firebase_ready
        return {
            "status": "healthy",
            "firebase": "connected" if is_firebase_ready() else "unavailable",
            "reports_last_7d": len(weekly),
            "reports_last_30d": len(monthly),
            "active_tenants": len(set(r.get("tenant_id") for r in monthly if r.get("tenant_id"))),
            "total_unique_reporters": len(set(r.get("created_by") for r in monthly if r.get("created_by"))),
        }

    def get_admin_tenants(self) -> List[Dict[str, Any]]:
        f30 = self._caan_filter(days=settings.DASHBOARD_ADMIN_TENANT_DAYS)
        reports = self.repo.get_all_in_range(f30)

        tenant_map: Dict[str, dict] = {}
        for r in reports:
            tid = r.get("tenant_id", "unknown")
            if tid not in tenant_map:
                tenant_map[tid] = {
                    "tenant_id": tid,
                    "total_reports": 0,
                    "ai_processed": 0,
                    "active_reporters": 0,
                    "high_risk_count": 0,
                    "last_report_date": None,
                }
            tm = tenant_map[tid]
            tm["total_reports"] += 1
            if r.get("ai_status") == "COMPLETED":
                tm["ai_processed"] += 1
            if r.get("severity") == "High":
                tm["high_risk_count"] += 1
            raw_date = r.get("created_at")
            if raw_date:
                if isinstance(raw_date, str):
                    raw_date = datetime.fromisoformat(raw_date)
                if tm["last_report_date"] is None or raw_date > tm["last_report_date"]:
                    tm["last_report_date"] = raw_date

        reporters: Dict[str, set] = {}
        for r in reports:
            tid = r.get("tenant_id", "unknown")
            uid = r.get("created_by")
            if uid:
                reporters.setdefault(tid, set()).add(uid)
        for tid, users in reporters.items():
            if tid in tenant_map:
                tenant_map[tid]["active_reporters"] = len(users)

        return sorted(tenant_map.values(), key=lambda t: t["total_reports"], reverse=True)

    def get_admin_usage(self) -> Dict[str, Any]:
        f = self._caan_filter(days=settings.DASHBOARD_ADMIN_USAGE_DAYS)
        reports = self.repo.get_all_in_range(f)
        return {
            "total_reports_30d": len(reports),
            "report_types": {
                "voluntary": sum(1 for r in reports if r.get("report_type") == "voluntary"),
                "mandatory": sum(1 for r in reports if r.get("report_type") == "mandatory"),
            },
            "status_breakdown": dict(
                (s, sum(1 for r in reports if r.get("status") == s))
                for s in set(r.get("status", "UNKNOWN") for r in reports)
            ),
            "monthly_usage": MetricsService.calculate_monthly_trends(reports),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base_filter(self, days: int = DEFAULT_DAYS, **overrides) -> ReportFilter:
        """Build a tenant-scoped filter with a default date range."""
        now = datetime.now(timezone.utc)
        date_from = now - timedelta(days=days)
        params = dict(
            tenant_id=self.tenant_id,
            cross_tenant=False,
            date_from=date_from,
            date_to=now,
        )
        params.update(overrides)
        logger.info(f"_base_filter: tenant_id={self.tenant_id}, days={days}, date_from={date_from}, date_to={now}")
        return ReportFilter(**params)

    def _caan_filter(self, days: int = DEFAULT_DAYS, **overrides) -> ReportFilter:
        """Build a cross-tenant filter for CAAN_SMD / SUPER_ADMIN."""
        now = datetime.now(timezone.utc)
        params = dict(
            tenant_id=None,
            cross_tenant=True,
            date_from=now - timedelta(days=days),
            date_to=now,
        )
        params.update(overrides)
        return ReportFilter(**params)

    @staticmethod
    def _tenant_report_counts(reports: List[dict]) -> List[Dict[str, Any]]:
        counts: Dict[str, int] = {}
        for r in reports:
            tid = r.get("tenant_id", "unknown")
            counts[tid] = counts.get(tid, 0) + 1
        return [
            {"tenant_id": tid, "report_count": cnt}
            for tid, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]

    @staticmethod
    def _tenant_severity_breakdown(reports: List[dict]) -> List[Dict[str, Any]]:
        from collections import defaultdict, Counter
        breakdown: Dict[str, Counter] = defaultdict(Counter)
        for r in reports:
            tid = r.get("tenant_id", "unknown")
            sev = r.get("severity", "Unspecified")
            breakdown[tid][sev] += 1
        return [
            {"tenant_id": tid, "severity_counts": dict(cnt)}
            for tid, cnt in sorted(breakdown.items())
        ]
