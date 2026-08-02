import sys
from datetime import datetime, timezone
from loguru import logger

from seed.config import OPERATOR_PROFILES, SEED_VERSION
from seed.generator import SeededRandom, generate_timestamp
from app.services.risk_matrix import _default_matrix_config, RISK_MATRIX_DOC_PATH


def create_tenant(db, profile: dict) -> dict:
    from app.core.config import settings
    tenant_id = profile["id"]
    tenant_ref = db.collection(settings.FIREBASE_COLLECTION_TENANTS).document(tenant_id)
    tenant_doc = tenant_ref.get()

    now = datetime.now(timezone.utc)

    tenant_data = {
        "name": profile["name"],
        "type": profile["type"],
        "icao": profile["icao"],
        "iata": profile.get("iata", ""),
        "country": profile["country"],
        "base": profile["base"],
        "fleet_size": profile["fleet_size"],
        "employees": profile["employees"],
        "survey_count": profile["survey_count"],
        "sms_profile": profile["culture_description"],
        "aircraft_types": profile["aircraft_types"],
        "routes": profile["routes"],
        "email_domain": profile["email_domain"],
        "created_at": now,
        "updated_at": now,
        "seed_version": SEED_VERSION,
        "active": True,
    }

    if not tenant_doc.exists:
        tenant_ref.set(tenant_data)
        logger.info(f"Created tenant: {profile['name']} ({tenant_id})")
    else:
        tenant_ref.update(tenant_data)
        logger.info(f"Updated tenant: {profile['name']} ({tenant_id})")

    info_data = {
        "tenant_name": profile["name"],
        "tenant_type": profile["type"],
        "icao_code": profile["icao"],
        "iata_code": profile.get("iata", ""),
        "base_airport": profile["base"],
        "fleet_size": profile["fleet_size"],
        "employee_count": profile["employees"],
        "safety_culture_index": None,
        "last_survey_date": None,
        "total_reports": 0,
        "registration": f"CAR-19/{profile['icao']}/{SEED_VERSION}",
        "seed_version": SEED_VERSION,
    }

    info_ref = tenant_ref.collection(settings.FIREBASE_COLLECTION_METADATA).document(
        settings.FIREBASE_DOCUMENT_INFO
    )
    info_ref.set(info_data, merge=True)

    risk_matrix_ref = tenant_ref.collection(settings.FIREBASE_COLLECTION_METADATA).document(
        RISK_MATRIX_DOC_PATH
    )
    risk_matrix_config = _default_matrix_config()
    risk_matrix_config["updated_by"] = "seed"
    risk_matrix_config["updated_at"] = now
    risk_matrix_ref.set(risk_matrix_config, merge=True)

    return tenant_id


def create_all_tenants(db) -> list:
    tenant_ids = []
    for profile in OPERATOR_PROFILES:
        tid = create_tenant(db, profile)
        tenant_ids.append(tid)
    logger.info(f"Seeded {len(tenant_ids)} tenants")
    return tenant_ids
