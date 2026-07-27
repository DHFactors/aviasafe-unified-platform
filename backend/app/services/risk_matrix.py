from typing import Optional, Dict, Any
from loguru import logger

from app.core.config import settings
from app.firebase import get_db, get_tenant_collection

RISK_MATRIX_DOC_PATH = "metadata/risk_matrix"

SEVERITY_LABELS_DEFAULT = {
    "1": "Negligible",
    "2": "Minor",
    "3": "Major",
    "4": "Hazardous",
    "5": "Catastrophic",
}

PROBABILITY_LABELS_DEFAULT = {
    "1": "Extremely Improbable",
    "2": "Improbable",
    "3": "Remote",
    "4": "Occasional",
    "5": "Frequent",
}

RISK_LEVEL_LABELS_DEFAULT = {
    "Low": "Low (Acceptable)",
    "Medium": "Medium (Tolerable)",
    "High": "High (Intolerable)",
    "Very High": "Very High (Intolerable – Immediate Action)",
}

RISK_LEVEL_COLORS_DEFAULT = {
    "Low": "#4CAF50",
    "Medium": "#FFC107",
    "High": "#FF9800",
    "Very High": "#F44336",
}

THRESHOLDS_DEFAULT = {
    "low_max": 5,
    "medium_max": 9,
    "high_max": 15,
}


def _default_matrix_config() -> dict:
    return {
        "version": "1.0",
        "severity_labels": dict(SEVERITY_LABELS_DEFAULT),
        "probability_labels": dict(PROBABILITY_LABELS_DEFAULT),
        "thresholds": dict(THRESHOLDS_DEFAULT),
        "risk_level_labels": dict(RISK_LEVEL_LABELS_DEFAULT),
        "risk_level_colors": dict(RISK_LEVEL_COLORS_DEFAULT),
    }


def compute_risk_index(severity: int, probability: int) -> int:
    return severity * probability


def get_risk_level(risk_index: int, thresholds: Optional[dict] = None) -> str:
    if thresholds is None:
        thresholds = THRESHOLDS_DEFAULT
    if risk_index <= thresholds["low_max"]:
        return "Low"
    elif risk_index <= thresholds["medium_max"]:
        return "Medium"
    elif risk_index <= thresholds["high_max"]:
        return "High"
    else:
        return "Very High"


def get_risk_matrix_config(tenant_id: str) -> dict:
    try:
        doc_ref = (
            get_tenant_collection(tenant_id, settings.FIREBASE_COLLECTION_METADATA)
            .document(RISK_MATRIX_DOC_PATH)
        )
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        logger.warning(f"Failed to load risk matrix for {tenant_id}: {e}")

    return _default_matrix_config()


def set_risk_matrix_config(tenant_id: str, config: dict, updated_by: str) -> dict:
    from datetime import datetime, timezone

    base = get_risk_matrix_config(tenant_id)
    base.update(config)
    base["updated_by"] = updated_by
    base["updated_at"] = datetime.now(timezone.utc).isoformat()

    doc_ref = (
        get_tenant_collection(tenant_id, settings.FIREBASE_COLLECTION_METADATA)
        .document(RISK_MATRIX_DOC_PATH)
    )
    doc_ref.set(base)
    return base


def get_icao_level_from_string(severity_str: Optional[str], risk_score: Optional[float]) -> int:
    mapping = {
        "Low": 2,
        "Medium": 3,
        "High": 4,
        "Critical": 5,
    }
    if severity_str and severity_str in mapping:
        return mapping[severity_str]
    if risk_score is not None:
        if risk_score <= 0.2:
            return 1
        elif risk_score <= 0.4:
            return 2
        elif risk_score <= 0.6:
            return 3
        elif risk_score <= 0.8:
            return 4
        else:
            return 5
    return 3


def get_icao_probability_from_likelihood(likelihood: Optional[str], risk_score: Optional[float]) -> int:
    mapping = {
        "Extremely Improbable": 1,
        "Improbable": 2,
        "Remote": 3,
        "Occasional": 4,
        "Frequent": 5,
        "Probable": 4,
    }
    if likelihood and likelihood in mapping:
        return mapping[likelihood]
    return get_icao_level_from_string(None, risk_score)
