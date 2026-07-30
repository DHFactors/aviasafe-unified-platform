from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from functools import lru_cache
from loguru import logger

from app.core.config import settings
from app.firebase import get_tenant_collection, get_cross_tenant_collection


class ReportFilter:
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        cross_tenant: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        occurrence_type: Optional[str] = None,
        page: int = 1,
        page_size: int = settings.REPO_DEFAULT_PAGE_SIZE,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        cursor: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.cross_tenant = cross_tenant
        self.date_from = date_from
        self.date_to = date_to
        self.report_type = report_type
        self.status = status
        self.severity = severity
        self.occurrence_type = occurrence_type
        self.page = max(page, 1)
        self.page_size = min(max(page_size, 1), settings.REPO_MAX_PAGE_SIZE)
        self.sort_by = sort_by
        self.sort_order = sort_order if sort_order in ("asc", "desc") else "desc"
        self.cursor = cursor

    def clone(self, **overrides) -> "ReportFilter":
        params = {
            "tenant_id": self.tenant_id,
            "cross_tenant": self.cross_tenant,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "report_type": self.report_type,
            "status": self.status,
            "severity": self.severity,
            "occurrence_type": self.occurrence_type,
            "page": self.page,
            "page_size": self.page_size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "cursor": self.cursor,
        }
        params.update(overrides)
        return ReportFilter(**params)


class ReportRepository:
    COLLECTION = settings.FIREBASE_COLLECTION_REPORTS

    _cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
    _CACHE_TTL_SECONDS = settings.REPO_CACHE_TTL_SECONDS

    def query_reports(self, filter: ReportFilter) -> Dict[str, Any]:
        try:
            base = self._build_collection(filter)
            query = self._apply_filters(base, filter)
            query = query.order_by(
                filter.sort_by, direction=self._sort_order(filter.sort_order)
            )

            count_query = query.count()
            count_result = count_query.get()
            total = count_result[0].value if count_result else 0

            if filter.cursor:
                parsed = self._parse_cursor(filter.cursor, filter)
                if parsed is not None:
                    query = query.start_after(parsed)

            query = query.limit(filter.page_size)

            docs = query.get()
            items = []
            last_doc = None
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                self._serialize_timestamps(data)
                items.append(data)
                last_doc = doc

            next_cursor = self._encode_cursor(last_doc, filter) if last_doc else None
            total_pages = max((total + filter.page_size - 1) // filter.page_size, 1)

            return {
                "items": items,
                "total": total,
                "page": filter.page,
                "page_size": filter.page_size,
                "total_pages": total_pages,
                "has_next": bool(next_cursor),
                "has_prev": filter.page > 1,
                "next_cursor": next_cursor,
            }
        except Exception as e:
            logger.error(f"ReportRepository.query_reports failed: {e}")
            raise

    def get_all_in_range(
        self,
        filter: ReportFilter,
        limit: int = settings.REPO_QUERY_LIMIT,
    ) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(filter)
        now = datetime.now().timestamp()
        cached = self._cache.get(cache_key)
        if cached and (now - cached[0]) < self._CACHE_TTL_SECONDS:
            logger.debug(f"Cache hit for {cache_key}")
            return cached[1]

        try:
            base = self._build_collection(filter)
            logger.debug(f"Firestore query: collection_group={filter.cross_tenant}, tenant_id={filter.tenant_id}, path='tenants/{filter.tenant_id}/{self.COLLECTION}', date_from={filter.date_from}, date_to={filter.date_to}")

            raw_all = list(base.limit(5000).stream())
            logger.debug(f"Raw doc count at tenants/{filter.tenant_id}/{self.COLLECTION} (no filters): {len(raw_all)}")
            if not raw_all:
                logger.warning(f"RAW COUNT IS ZERO — collection tenants/{filter.tenant_id}/{self.COLLECTION} is empty or does not exist. Check tenant_id format vs Firestore path.")

            query = self._apply_filters(base, filter)
            query = query.order_by(
                filter.sort_by, direction=self._sort_order(filter.sort_order)
            ).limit(limit)

            docs = query.get()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                self._serialize_timestamps(data)
                results.append(data)

            if len(results) == 0 and len(raw_all) > 0 and (filter.date_from or filter.date_to):
                logger.warning(f"Date filter ({filter.date_from} to {filter.date_to}) returned 0 results but {len(raw_all)} docs exist unfiltered. Retrying without date filter (likely ISO-string timestamps or old seed data).")
                unfiltered = []
                for doc in raw_all:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    self._serialize_timestamps(data)
                    unfiltered.append(data)
                results = unfiltered

            self._cache[cache_key] = (now, results)
            if len(results) == 0:
                logger.warning(f"Firestore query returned 0 results for tenant_id={filter.tenant_id}, cross_tenant={filter.cross_tenant}, date_from={filter.date_from}, date_to={filter.date_to}")
            logger.debug(f"Cached {len(results)} results for {cache_key}")
            return results
        except Exception as e:
            logger.error(f"ReportRepository.get_all_in_range failed: {e}")
            raise

    def invalidate_cache(self, prefix: Optional[str] = None):
        if prefix:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(prefix)}
        else:
            self._cache.clear()
        logger.debug("Repository cache invalidated")

    def get_by_id(self, report_id: str, filter: ReportFilter) -> Optional[Dict[str, Any]]:
        try:
            if filter.cross_tenant:
                docs = get_cross_tenant_collection(self.COLLECTION).where(
                    "__name__", "==", report_id
                ).get()
                if not docs:
                    return None
                data = docs[0].to_dict()
                data["id"] = docs[0].id
            else:
                doc = (
                    get_tenant_collection(filter.tenant_id, self.COLLECTION)
                    .document(report_id)
                    .get()
                )
                if not doc.exists:
                    return None
                data = doc.to_dict()
                data["id"] = doc.id

            self._serialize_timestamps(data)
            return data
        except Exception as e:
            logger.error(f"ReportRepository.get_by_id({report_id}) failed: {e}")
            raise

    def count_by_status(self, filter: ReportFilter) -> Dict[str, int]:
        base = self._build_collection(filter)
        query = self._apply_filters(base, filter)
        count_result = query.count().get()
        return {"total": count_result[0].value if count_result else 0}

    def count_by_severity(self, filter: ReportFilter) -> Dict[str, int]:
        base = self._build_collection(filter)
        query = self._apply_filters(base, filter)
        count_result = query.count().get()
        return {"total": count_result[0].value if count_result else 0}

    def _build_collection(self, filter: ReportFilter):
        if filter.cross_tenant:
            return get_cross_tenant_collection(self.COLLECTION)
        return get_tenant_collection(filter.tenant_id, self.COLLECTION)

    def _apply_filters(self, collection, filter: ReportFilter):
        query = collection
        if filter.date_from:
            query = query.where(filter.sort_by, ">=", filter.date_from)
        if filter.date_to:
            query = query.where(filter.sort_by, "<=", filter.date_to)
        if filter.report_type:
            query = query.where("report_type", "==", filter.report_type)
        if filter.status:
            query = query.where("status", "==", filter.status)
        if filter.severity:
            query = query.where("severity", "==", filter.severity)
        if filter.occurrence_type:
            query = query.where("occurrence_type", "==", filter.occurrence_type)
        return query

    @staticmethod
    def _sort_order(order: str):
        from google.cloud.firestore import Query
        return Query.DESCENDING if order == "desc" else Query.ASCENDING

    @staticmethod
    def _encode_cursor(doc, filter: ReportFilter) -> Optional[str]:
        if doc is None:
            return None
        sort_val = doc.get(filter.sort_by)
        if sort_val is None:
            return None
        if hasattr(sort_val, "isoformat"):
            sort_val = sort_val.isoformat()
        return sort_val

    @staticmethod
    def _parse_cursor(cursor: str, filter: ReportFilter):
        target = cursor
        if filter.sort_by == "created_at" or filter.sort_by == "occurrence_date":
            try:
                return datetime.fromisoformat(target)
            except (ValueError, TypeError):
                return None
        return target

    @staticmethod
    def _cache_key(filter: ReportFilter) -> str:
        parts = [
            str(filter.tenant_id or "cross"),
            str(filter.cross_tenant),
            str(filter.date_from.isoformat() if filter.date_from else ""),
            str(filter.date_to.isoformat() if filter.date_to else ""),
            str(filter.report_type or ""),
            str(filter.status or ""),
            str(filter.severity or ""),
            str(filter.occurrence_type or ""),
            filter.sort_by,
            filter.sort_order,
        ]
        return "::".join(parts)

    @staticmethod
    def _serialize_timestamps(data: dict) -> None:
        for key in (
            "created_at", "updated_at", "occurrence_date",
            "processed_at", "reviewed_at",
        ):
            if key in data and hasattr(data[key], "isoformat"):
                data[key] = data[key].isoformat()
