# ============================================================================
# FILE: report.py
# PATH: backend/app/models/report.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-03
# PURPOSE: Pydantic models for safety report data with Firebase compatibility.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReportType(str, Enum):
    VOLUNTARY = "voluntary"
    MANDATORY = "mandatory"

class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SUBMITTED = "submitted_to_authority"
    FAILED = "failed"

class ReportCreate(BaseModel):
    """Model for creating a new safety report."""
    narrative: str = Field(..., min_length=10, max_length=10000)
    location: str = Field(..., min_length=3, max_length=100)
    date: datetime
    report_type: ReportType = ReportType.VOLUNTARY
    is_anonymous: bool = False
    flight_number: Optional[str] = None
    aircraft_registration: Optional[str] = None
    files: Optional[List[str]] = None
    
    @validator('narrative')
    def sanitize_narrative(cls, v: str) -> str:
        """Remove potential PII and injection attempts."""
        # Remove script tags
        v = v.replace('<script>', '').replace('</script>', '')
        # Remove common PII patterns (basic protection)
        import re
        v = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', v)
        v = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', v)
        return v

class ReportResponse(BaseModel):
    """Model for report response."""
    id: str
    narrative: str
    location: str
    date: datetime
    report_type: ReportType
    status: ReportStatus
    classification: Optional[Dict[str, Any]]
    mandatory_check: Optional[Dict[str, Any]]
    submitted_at: datetime
    processed_at: Optional[datetime]
    is_anonymous: bool
    tenant_id: str
    submitter_id: Optional[str]

class ClassificationResult(BaseModel):
    """Model for AI classification results."""
    occurrence_type: Optional[str]
    human_factors: List[str] = []
    risk_level: str = "Medium"
    phase_of_flight: Optional[str]
    confidence: float = 0.0
    summary: Optional[str]
    recommendations: List[str] = []

class MandatoryCheckResult(BaseModel):
    """Model for mandatory vs voluntary classification."""
    is_mandatory: bool = False
    category: Optional[str]  # 'A' or 'B'
    reason: Optional[str]
    matched_criteria: List[str] = []
    confidence: float = 0.0
