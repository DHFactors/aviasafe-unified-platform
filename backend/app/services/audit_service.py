from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from loguru import logger

from app.firebase import get_db

AUDIT_COLLECTION = "audit_logs"


def request_context(request) -> Tuple[Optional[str], Optional[str]]:
    """Return (client_ip, request_id) from a FastAPI Request."""
    if request is None:
        return None, None
    client = getattr(request, "client", None)
    ip = client.host if client else None
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = request.headers.get("X-Request-ID")
    return ip, request_id or None


def log_audit(
    *,
    action: str,
    user: Optional[str] = None,
    tenant_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    ip: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Append an entry to the Firestore `audit_logs` collection.

    Failures to persist an audit entry must never break the business request,
    so the write is best-effort and only logged as a warning.
    """
    try:
        db = get_db()
        entry = {
            "action": action,
            "user": user,
            "tenant_id": tenant_id,
            "target_type": target_type,
            "target_id": target_id,
            "ip": ip,
            "request_id": request_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
        db.collection(AUDIT_COLLECTION).add(entry)
    except Exception as e:
        logger.warning(f"Audit log write failed for action={action}: {e}")
