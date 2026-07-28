# ============================================================================
# FILE: admin.py
# PATH: backend/app/routes/admin.py
# VERSION: 2.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-27
# PURPOSE: Admin and Safety Manager endpoints for system configuration.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from loguru import logger
from datetime import datetime, timezone

from app.firebase import get_auth, get_db
from app.middleware.auth import get_safety_manager, get_admin_user
from app.services.risk_matrix import (
    get_risk_matrix_config,
    set_risk_matrix_config,
    THRESHOLDS_DEFAULT,
)

router = APIRouter()


class RiskMatrixThresholds(BaseModel):
    low_max: int = Field(default=5, ge=1, le=25)
    medium_max: int = Field(default=9, ge=1, le=25)
    high_max: int = Field(default=15, ge=1, le=25)


class RiskMatrixConfig(BaseModel):
    thresholds: RiskMatrixThresholds
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/risk-matrix")
async def get_risk_matrix(
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    """Get the ICAO risk matrix configuration for the user's tenant.

    Defaults to ICAO-aligned thresholds if not yet configured.
    """
    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"]:
        tenant_id = "default"
    config = get_risk_matrix_config(tenant_id)
    return config


@router.put("/risk-matrix", status_code=status.HTTP_200_OK)
async def update_risk_matrix(
    config: RiskMatrixConfig,
    user: Dict[str, Any] = Depends(get_safety_manager),
):
    """Update the ICAO risk matrix thresholds for the user's tenant.

    Thresholds define Low/Medium/High/Very High boundaries.
    All thresholds are inclusive max values for each level.
    Must satisfy: 1 <= low_max < medium_max < high_max <= 25.
    """
    t = config.thresholds
    if not (1 <= t.low_max < t.medium_max < t.high_max <= 25):
        raise HTTPException(
            status_code=400,
            detail="Thresholds must satisfy: 1 <= low_max < medium_max < high_max <= 25",
        )

    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") in ["CAAN_SMD", "SUPER_ADMIN"]:
        tenant_id = "default"

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "thresholds": t.model_dump(),
        "updated_by": user["uid"],
        "updated_at": now,
    }
    set_risk_matrix_config(tenant_id, data)
    logger.info(f"Risk matrix updated for tenant {tenant_id} by {user['uid']}")
    return data


class SetupClaimsRequest(BaseModel):
    setup_key: str
    users: List[dict]


SETUP_SECRET = "aviasafe-e2e-setup-2026"


@router.post("/setup-claims")
async def setup_test_user_claims(req: SetupClaimsRequest):
    """One-time endpoint to set custom claims on test users.
    Protected by a setup key to prevent unauthorized use.
    """
    if req.setup_key != SETUP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid setup key")

    results = []
    auth = get_auth()
    for u in req.users:
        email = u.get("email")
        role = u.get("role", "USER")
        tenant_id = u.get("tenant_id")
        if not email:
            results.append({"email": email, "status": "error", "detail": "email required"})
            continue
        try:
            user_record = auth.get_user_by_email(email)
            claims = {"role": role}
            if tenant_id:
                claims["tenant_id"] = tenant_id
            auth.set_custom_user_claims(user_record.uid, claims)
            results.append({"email": email, "uid": user_record.uid, "role": role, "tenant_id": tenant_id, "status": "ok"})
            logger.info(f"Claims set for {email}: role={role}, tenant_id={tenant_id}")
        except Exception as e:
            results.append({"email": email, "status": "error", "detail": str(e)})
            logger.error(f"Failed to set claims for {email}: {e}")

    return {"success": True, "results": results}


class ProvisionRequest(BaseModel):
    setup_key: str


AIRLINES = [
    {"id": "buddha-air", "name": "Buddha Air", "icao": "BHA", "email": "buddhaair@buddhaair.com"},
    {"id": "nepal-airlines", "name": "Nepal Airlines", "icao": "NAL", "email": "info@nac.com.np"},
    {"id": "shree-airlines", "name": "Shree Airlines", "icao": "SHA", "email": "info@shreeairlines.com"},
    {"id": "sita-air", "name": "Sita Air", "icao": "STA", "email": "info@sitaair.com"},
    {"id": "summit-air", "name": "Summit Air", "icao": "SMT", "email": "info@summitair.com.np"},
    {"id": "tara-air", "name": "Tara Air", "icao": "TRA", "email": "info@taraair.com"},
    {"id": "yeti-airlines", "name": "Yeti Airlines", "icao": "YET", "email": "info@yetiairlines.com"},
    {"id": "makalu-air", "name": "Makalu Air", "icao": "MKU", "email": "info@makaluair.com"},
    {"id": "himalaya-airlines", "name": "Himalaya Airlines", "icao": "HIM", "email": "info@himalaya-airlines.com"},
    {"id": "air-dynasty", "name": "Air Dynasty Heli Services", "icao": "ADH", "email": "info@airdynasty.com"},
    {"id": "altitude-air", "name": "Altitude Air", "icao": "ALT", "email": "info@altitudeair.com.np"},
    {"id": "annapurna-heli", "name": "Annapurna Helicopter", "icao": "ANH", "email": "info@annapurnaheli.com"},
    {"id": "fishtail-air", "name": "Fishtail Air", "icao": "FTA", "email": "info@fishtailair.com"},
    {"id": "heli-everest", "name": "Heli Everest", "icao": "HLE", "email": "info@helieverest.com"},
    {"id": "kailash-helicopter", "name": "Kailash Helicopter Services", "icao": "KHS", "email": "info@kailashhelicopter.com"},
    {"id": "manang-air", "name": "Manang Air", "icao": "MNA", "email": "info@manangair.com"},
    {"id": "mountain-helicopters", "name": "Mountain Helicopters", "icao": "MTH", "email": "info@mountainhelicopters.com"},
    {"id": "mustang-helicopter", "name": "Mustang Helicopter", "icao": "MSH", "email": "info@mustanghelicopter.com"},
    {"id": "prabhu-helicopters", "name": "Prabhu Helicopters", "icao": "PRB", "email": "info@prabhuhelicopters.com"},
    {"id": "simrik-air", "name": "Simrik Air", "icao": "SMK", "email": "info@simrikair.com"},
]

STANDARD_PASSWORD = "AviaSAFE2026!Secure"


@router.post("/provision-airlines", status_code=status.HTTP_200_OK)
async def provision_20_airlines(req: ProvisionRequest):
    """Batch-provision all 20 Nepali airlines: create Auth users, set claims, create Firestore tenants."""
    if req.setup_key != SETUP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid setup key")

    auth = get_auth()
    db = get_db()
    results = []
    now = datetime.now(timezone.utc).isoformat()

    for a in AIRLINES:
        tid = a["id"]
        email = a["email"]
        name = a["name"]
        icao = a["icao"]
        record = {"tenant_id": tid, "email": email, "name": name, "status": "pending"}

        try:
            user = auth.create_user(
                email=email,
                password=STANDARD_PASSWORD,
                email_verified=True,
                display_name=f"{name} Safety Manager",
            )
            uid = user.uid

            auth.set_custom_user_claims(uid, {"role": "AIRLINE_ADMIN", "tenant_id": tid})

            db.collection("tenants").document(tid).set({
                "tenant_id": tid,
                "name": name,
                "icao": icao,
                "country": "Nepal",
                "active": True,
                "safety_manager": {
                    "email": email,
                    "name": f"{name} Safety Manager",
                    "uid": uid,
                },
                "survey_config": {
                    "open": True,
                    "open_date": "2026-08-01",
                    "close_date": "2026-08-31",
                },
                "created_at": now,
                "updated_at": now,
            })

            record["uid"] = uid
            record["status"] = "ok"
            logger.info(f"Provisioned {name} ({tid}) -> {email} / {uid}")

        except auth.EmailAlreadyExistsError:
            record["status"] = "skipped"
            record["detail"] = "email already exists"
            logger.warning(f"Provision skipped for {email}: already exists")
        except Exception as e:
            record["status"] = "error"
            record["detail"] = str(e)
            logger.error(f"Provision failed for {email}: {e}")

        results.append(record)

    summary = {
        "total": len(AIRLINES),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "error": sum(1 for r in results if r["status"] == "error"),
    }

    return {"success": True, "summary": summary, "results": results}
