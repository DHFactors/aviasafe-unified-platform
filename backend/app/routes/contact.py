# ============================================================================
# FILE: contact.py
# PATH: backend/app/routes/contact.py
# PURPOSE: Public contact form endpoint. Validates the submitted message and
#          pushes the contact into Sender.net (REST API v2) so AviaSAFE can
#          follow up from the marketing account. The Sender API key is read
#          from the environment (SENDER_API_KEY) and is never exposed to the
#          browser — the frontend posts to this endpoint instead.
# AUTHOR: AviaSAFE Systems
# ============================================================================

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from loguru import logger

from app.core.config import settings

router = APIRouter()


class ContactMessage(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


def _envelope(data: Any) -> Dict[str, Any]:
    return {
        "status": "success",
        "timestamp": datetime.now(),
        "data": data,
    }


def _split_name(name: str):
    """Best-effort split of a full name into first/last for the Sender subscriber."""
    parts = [p.strip() for p in name.replace("\t", " ").split() if p.strip()]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _send_to_sender(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST the subscriber to Sender.net v2. Raises on network / API failure."""
    api_key = (settings.SENDER_API_KEY or "").strip()
    if not api_key:
        raise RuntimeError("SENDER_API_KEY is not configured on the server")

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        settings.SENDER_API_BASE_URL + "/subscribers",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Cloudflare on api.sender.net blocks the default urllib user-agent.
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            status_code = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Sender API returned HTTP {e.code}: {raw}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Sender API unreachable: {e.reason}")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {}
    if status_code not in (200, 201) or result.get("success") is False:
        raise RuntimeError(f"Sender API returned HTTP {status_code}: {raw}")
    return result


@router.post("", status_code=status.HTTP_200_OK)
async def submit_contact_form(message: ContactMessage):
    """Accept a public contact form submission and forward it to Sender.net.

    No authentication is required — this is the public 'Contact Us' endpoint.
    The visitor is created as a Sender subscriber (email + name) and the
    subject/message are stored as custom fields for the marketing team. The
    endpoint never returns the Sender API key or any internal error detail.
    """
    name = message.name.strip()
    first, last = _split_name(name)

    fields = {}
    if message.subject:
        fields["Subject"] = message.subject
    if message.message:
        fields["Message"] = message.message

    payload: Dict[str, Any] = {
        "email": str(message.email).strip().lower(),
        "firstname": first,
        "lastname": last,
        "trigger_automation": False,
    }
    if fields:
        payload["fields"] = fields
    list_id = (settings.SENDER_LIST_ID or "").strip()
    if list_id:
        payload["groups"] = [list_id]

    try:
        result = _send_to_sender(payload)
    except RuntimeError as e:
        logger.error(f"Contact form -> Sender.net failed for {message.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We could not deliver your message right now. Please try again later.",
        )

    logger.info(f"Contact form received from {message.email} (name={name})")
    return _envelope({"ok": True, "sender": result.get("success", False)})
