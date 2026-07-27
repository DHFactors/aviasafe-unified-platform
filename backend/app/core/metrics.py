import time
from typing import Dict, Tuple, Any
from collections import defaultdict
from fastapi import APIRouter, Depends

from app.middleware.auth import get_admin_user

router = APIRouter()

_requests_total: Dict[Tuple[str, str, int], int] = defaultdict(int)
_request_duration_buckets: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
_ai_failures: int = 0
_ai_total: int = 0
_firestore_latency: list = []

BUCKETS_MS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]


def record_request(method: str, path: str, status: int, duration_ms: float):
    key = (method, path, status)
    _requests_total[key] += 1

    for bucket in BUCKETS_MS:
        if duration_ms <= bucket:
            _request_duration_buckets[f"{method} {path}"][bucket] += 1
            break


def record_ai_result(success: bool):
    global _ai_total, _ai_failures
    _ai_total += 1
    if not success:
        _ai_failures += 1


def record_firestore_latency(duration_ms: float):
    _firestore_latency.append(duration_ms)
    if len(_firestore_latency) > 1000:
        _firestore_latency.pop(0)


def _avg(lst: list) -> float:
    return round(sum(lst) / len(lst), 2) if lst else 0.0


def _p99(lst: list) -> float:
    if not lst:
        return 0.0
    sorted_lst = sorted(lst)
    idx = int(len(sorted_lst) * 0.99)
    return sorted_lst[min(idx, len(sorted_lst) - 1)]


@router.get("/metrics")
async def metrics(user: Dict[str, Any] = Depends(get_admin_user)):
    lines = ["# AviaSAFE SSP API Metrics"]
    lines.append(f"# TYPE requests_total counter")
    for (method, path, status), count in sorted(_requests_total.items()):
        lines.append(f'requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

    lines.append(f"# TYPE request_duration_ms histogram")
    for route, buckets in sorted(_request_duration_buckets.items()):
        for bucket_ms, count in sorted(buckets.items()):
            lines.append(f'request_duration_ms{{route="{route}",le="{bucket_ms}"}} {count}')

    lines.append(f"# TYPE ai_failures counter")
    lines.append(f"ai_failures_total {_ai_failures}")
    lines.append(f"ai_requests_total {_ai_total}")
    ai_success_rate = round((_ai_total - _ai_failures) / max(_ai_total, 1) * 100, 1)
    lines.append(f"ai_success_rate_percent {ai_success_rate}")

    if _firestore_latency:
        lines.append(f"# TYPE firestore_latency_ms gauge")
        lines.append(f"firestore_latency_avg_ms {_avg(_firestore_latency)}")
        lines.append(f"firestore_latency_p99_ms {_p99(_firestore_latency)}")

    return "\n".join(lines) + "\n"
