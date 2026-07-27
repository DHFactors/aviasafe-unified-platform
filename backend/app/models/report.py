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


_OCCURRENCE_TYPES = [
    "Runway Excursion", "Runway Incursion", "Airborne Conflict",
    "Abnormal Runway Contact", "Ground Collision", "System/Component Failure",
    "Powerplant Failure", "Weather Encounter", "Bird Strike",
    "Cabin Safety Event", "Procedural Deviation", "ATC Operational Incident",
    "Other"
]

_OCCURRENCE_CLASSES = ["ACCIDENT", "SERIOUS_INCIDENT", "INCIDENT"]

_OCCURRENCE_CATEGORIES = [
    "ARC", "MAC", "BIRD", "CABIN", "CFIT", "ENG", "FIRE", "GCOL",
    "LOCI", "PRO", "RE", "RI", "SYS", "WX", "OTHER"
]

_SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]

_INVESTIGATION_STATUSES = [
    "NOT_INVESTIGATED", "INVESTIGATING", "INVESTIGATED", "CLOSED"
]

_FLIGHT_PHASES = [
    "Standing", "Pushback/Towing", "Taxi", "Takeoff", "Initial Climb",
    "Climb", "Cruise", "Descent", "Approach", "Landing", "Go-Around",
    "Emergency", "Hover", "Circuit", "Aerobatics"
]

_FLIGHT_TYPES = ["Commercial", "Private", "Training", "Cargo", "Ferry", "Other"]

_AIRCRAFT_CATEGORIES = ["Aeroplane", "Helicopter", "Glider", "Drone", "Other"]

_HUMAN_FACTORS = [
    "Decision Making Error", "Situational Awareness", "Skill-Based Error",
    "Procedural Error", "Communication", "Fatigue", "Pressure",
    "Distraction", "Perception"
]

_REPORTER_ROLES = [
    "pilot", "first_officer", "flight_engineer", "cabin_crew",
    "atc", "maintenance", "ground", "dispatcher", "safety_manager", "other"
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
    severity: int
    probability: int
    risk_index: int
    risk_level: str
    assessed_by: str
    assessed_at: datetime
    notes: Optional[str] = None


class AiSuggestedAssessment(BaseModel):
    suggested_severity: int
    suggested_probability: int
    suggested_risk_index: int
    suggested_risk_level: str
    confidence: float
    severity_explanation: Optional[str] = None
    probability_explanation: Optional[str] = None


class ReportCreate(BaseModel):
    narrative: str = Field(..., min_length=10, max_length=10000)
    location: str = Field(..., min_length=3, max_length=100)
    occurrence_date: datetime
    report_type: ReportType = ReportType.VOLUNTARY
    is_anonymous: bool = False
    flight_number: Optional[str] = None
    aircraft_registration: Optional[str] = None
    severity_level: Optional[int] = None
    probability_level: Optional[int] = None

    occurrence_class: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None

    aircraft_make: Optional[str] = None
    aircraft_model: Optional[str] = None
    aircraft_serial_number: Optional[str] = None
    operator: Optional[str] = None
    operator_icao: Optional[str] = None
    aircraft_category: Optional[str] = None
    engine_make: Optional[str] = None
    engine_model: Optional[str] = None
    engine_serial_number: Optional[str] = None

    flight_phase: Optional[str] = None
    flight_type: Optional[str] = None
    departure_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    aircraft_utilisation_hours: Optional[float] = None
    aircraft_utilisation_cycles: Optional[int] = None

    crew_count: Optional[int] = None
    passenger_count: Optional[int] = None
    fatal_injuries: Optional[int] = None
    serious_injuries: Optional[int] = None
    minor_injuries: Optional[int] = None

    occurrence_category: Optional[str] = None
    human_factors: Optional[List[str]] = None
    contributing_factors: Optional[List[str]] = None
    investigation_agency: Optional[str] = None

    reporter_name: Optional[str] = None
    reporter_role: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_organisation: Optional[str] = None
    reporting_date: Optional[datetime] = None

    @field_validator('narrative')
    def sanitize_narrative(cls, v: str) -> str:
        v = v.replace('<script>', '').replace('</script>', '')
        import re
        v = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', v)
        v = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', v)
        return v

    @field_validator('occurrence_category')
    def validate_occurrence_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _OCCURRENCE_CATEGORIES:
            raise ValueError(f"occurrence_category must be one of: {', '.join(_OCCURRENCE_CATEGORIES)}")
        return v

    @field_validator('occurrence_class')
    def validate_occurrence_class(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _OCCURRENCE_CLASSES:
            raise ValueError(f"occurrence_class must be one of: {', '.join(_OCCURRENCE_CLASSES)}")
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

    @field_validator('flight_phase')
    def validate_flight_phase(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _FLIGHT_PHASES:
            raise ValueError(f"flight_phase must be one of: {', '.join(_FLIGHT_PHASES)}")
        return v

    @field_validator('flight_type')
    def validate_flight_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _FLIGHT_TYPES:
            raise ValueError(f"flight_type must be one of: {', '.join(_FLIGHT_TYPES)}")
        return v

    @field_validator('aircraft_category')
    def validate_aircraft_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _AIRCRAFT_CATEGORIES:
            raise ValueError(f"aircraft_category must be one of: {', '.join(_AIRCRAFT_CATEGORIES)}")
        return v

    @field_validator('reporter_role')
    def validate_reporter_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _REPORTER_ROLES:
            raise ValueError(f"reporter_role must be one of: {', '.join(_REPORTER_ROLES)}")
        return v

    @field_validator('human_factors')
    def validate_human_factors(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for hf in v:
                if hf not in _HUMAN_FACTORS:
                    raise ValueError(f"human_factor '{hf}' must be one of: {', '.join(_HUMAN_FACTORS)}")
        return v


class AiAnalysisResult(BaseModel):
    occurrence_type: Optional[str] = None
    human_factors: List[str] = []
    risk_level: str = "Medium"
    phase_of_flight: Optional[str] = None
    confidence: float = 0.0
    summary: Optional[str] = None
    recommendations: List[str] = []
    mandatory_check: Optional[Dict[str, Any]] = None


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
    investigation_status: Optional[str] = None
    severity_level: Optional[int] = None
    probability_level: Optional[int] = None
    risk_index: Optional[int] = None
    risk_level: Optional[str] = None
    risk_assessment: Optional[RiskAssessment] = None
    ai_suggested_assessment: Optional[AiSuggestedAssessment] = None
    ai_analysis: Optional[AiAnalysisResult] = None

    occurrence_class: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None

    aircraft_make: Optional[str] = None
    aircraft_model: Optional[str] = None
    aircraft_serial_number: Optional[str] = None
    operator: Optional[str] = None
    operator_icao: Optional[str] = None
    aircraft_category: Optional[str] = None
    engine_make: Optional[str] = None
    engine_model: Optional[str] = None
    engine_serial_number: Optional[str] = None

    flight_phase: Optional[str] = None
    flight_type: Optional[str] = None
    departure_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    aircraft_utilisation_hours: Optional[float] = None
    aircraft_utilisation_cycles: Optional[int] = None

    crew_count: Optional[int] = None
    passenger_count: Optional[int] = None
    fatal_injuries: Optional[int] = None
    serious_injuries: Optional[int] = None
    minor_injuries: Optional[int] = None

    occurrence_category: Optional[str] = None
    human_factors: Optional[List[str]] = None
    contributing_factors: Optional[List[str]] = None
    investigation_agency: Optional[str] = None

    reporter_name: Optional[str] = None
    reporter_role: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_organisation: Optional[str] = None
    reporting_date: Optional[datetime] = None

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
    occurrence_category: Optional[str] = None
    aircraft_make: Optional[str] = None
    aircraft_model: Optional[str] = None
    operator: Optional[str] = None
    flight_phase: Optional[str] = None
