from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    VOLUNTARY = "voluntary"
    MANDATORY = "mandatory"


class ReportStatus(str, Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class AiStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


_OCCURRENCE_TYPES = [
    "Runway Excursion", "Runway Incursion", "Airborne Conflict",
    "Abnormal Runway Contact", "Ground Collision", "System/Component Failure",
    "Powerplant Failure", "Weather Encounter", "Bird Strike",
    "Cabin Safety Event", "Procedural Deviation", "ATC Operational Incident",
    "Other"
]

_SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]

_INVESTIGATION_STATUSES = [
    "NOT_INVESTIGATED", "INVESTIGATING", "INVESTIGATED", "CLOSED"
]


class Attachment(BaseModel):
    name: str
    url: str
    type: str = "unknown"


class CorrectiveAction(BaseModel):
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "OPEN"


class RiskAssessment(BaseModel):
    severity: int  # 1-5 ICAO
    probability: int  # 1-5 ICAO
    risk_index: int  # 1-25
    risk_level: str  # "Low" | "Medium" | "High" | "Very High"
    assessed_by: str
    assessed_at: datetime
    notes: Optional[str] = None


class AiSuggestedAssessment(BaseModel):
    suggested_severity: int  # 1-5
    suggested_probability: int  # 1-5
    suggested_risk_index: int  # 1-25
    suggested_risk_level: str
    confidence: float  # 0.0-1.0
    severity_explanation: Optional[str] = None  # ICAO-grounded reasoning
    probability_explanation: Optional[str] = None  # ICAO-grounded reasoning


class ReportCreate(BaseModel):
    narrative: str = Field(..., min_length=10, max_length=10000)
    location: str = Field(..., min_length=3, max_length=100)
    occurrence_date: datetime
    report_type: ReportType = ReportType.VOLUNTARY
    is_anonymous: bool = False
    flight_number: Optional[str] = None
    aircraft_registration: Optional[str] = None
    occurrence_type: Optional[str] = None
    severity: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    risk_score: Optional[float] = None
    likelihood: Optional[str] = None
    consequence: Optional[str] = None
    bowtie_hazard: Optional[str] = None
    bowtie_barrier: Optional[str] = None
    sms_category: Optional[str] = None
    severity_level: Optional[int] = None  # 1-5 ICAO
    probability_level: Optional[int] = None  # 1-5 ICAO

    @field_validator('narrative')
    def sanitize_narrative(cls, v: str) -> str:
        v = v.replace('<script>', '').replace('</script>', '')
        import re
        v = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', v)
        v = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', v)
        return v

    @field_validator('occurrence_type')
    def validate_occurrence_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _OCCURRENCE_TYPES:
            raise ValueError(f"occurrence_type must be one of: {', '.join(_OCCURRENCE_TYPES)}")
        return v

    @field_validator('severity')
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _SEVERITY_LEVELS:
            raise ValueError(f"severity must be one of: {', '.join(_SEVERITY_LEVELS)}")
        return v

    @field_validator('risk_score')
    def validate_risk_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("risk_score must be between 0.0 and 1.0")
        return v

    @field_validator('severity_level')
    def validate_severity_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("severity_level must be between 1 and 5")
        return v

    @field_validator('probability_level')
    def validate_probability_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("probability_level must be between 1 and 5")
        return v

    @field_validator('flight_number')
    def validate_flight_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            return None
        return v

    @field_validator('aircraft_registration')
    def validate_aircraft_registration(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            return None
        return v.upper() if v else v


class AiAnalysisResult(BaseModel):
    occurrence_type: Optional[str] = None
    human_factors: List[str] = []
    risk_level: str = "Medium"
    phase_of_flight: Optional[str] = None
    confidence: float = 0.0
    summary: Optional[str] = None
    recommendations: List[str] = []
    mandatory_check: Optional[Dict[str, Any]] = None
    ai_model: Optional[str] = None
    prompt_version: Optional[str] = None
    processing_time_ms: Optional[float] = None
    processed_at: Optional[datetime] = None


class ReportResponse(BaseModel):
    id: str
    tenant_id: str
    report_type: ReportType
    status: ReportStatus
    ai_status: AiStatus
    narrative: str
    location: str
    occurrence_date: datetime
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_anonymous: bool = False
    flight_number: Optional[str] = None
    aircraft_registration: Optional[str] = None
    occurrence_type: Optional[str] = None
    severity: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    risk_score: Optional[float] = None
    likelihood: Optional[str] = None
    consequence: Optional[str] = None
    bowtie_hazard: Optional[str] = None
    bowtie_barrier: Optional[str] = None
    sms_category: Optional[str] = None
    investigation_status: Optional[str] = None
    corrective_actions: Optional[List[CorrectiveAction]] = None
    lessons_learned: Optional[List[str]] = None
    safety_action_required: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ai_analysis: Optional[AiAnalysisResult] = None
    severity_level: Optional[int] = None
    probability_level: Optional[int] = None
    risk_index: Optional[int] = None
    risk_level: Optional[str] = None
    risk_assessment: Optional[RiskAssessment] = None
    ai_suggested_assessment: Optional[AiSuggestedAssessment] = None

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    tenant_id: str
    report_type: ReportType
    status: ReportStatus
    ai_status: AiStatus
    location: str
    occurrence_date: datetime
    created_by: str
    created_at: datetime
    is_anonymous: bool
    occurrence_type: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    severity_level: Optional[int] = None
    probability_level: Optional[int] = None



