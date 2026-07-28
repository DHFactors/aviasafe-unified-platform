from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DeficiencySeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DeficiencyStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    UNDER_REVIEW = "Under Review"
    CLOSED = "Closed"


class SafetyDeficiencyCreate(BaseModel):
    tenant_id: str = Field(...)
    event_id: Optional[str] = None
    source: str = Field(...)
    hazard_code: Optional[str] = None
    description: str = Field(..., min_length=10)
    taxonomy_main: Optional[str] = None
    taxonomy_type: Optional[str] = None
    taxonomy_specific: Optional[str] = None
    unsafe_event: Optional[str] = None
    identified_hazard: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^[HML]$")
    severity: Optional[DeficiencySeverity] = None
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: DeficiencyStatus = DeficiencyStatus.OPEN
    remarks: Optional[str] = None
    csd_remarks: Optional[str] = None


class SafetyDeficiencyUpdate(BaseModel):
    hazard_code: Optional[str] = None
    description: Optional[str] = None
    taxonomy_main: Optional[str] = None
    taxonomy_type: Optional[str] = None
    taxonomy_specific: Optional[str] = None
    unsafe_event: Optional[str] = None
    identified_hazard: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[DeficiencySeverity] = None
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[DeficiencyStatus] = None
    remarks: Optional[str] = None
    csd_remarks: Optional[str] = None


class SafetyDeficiencyResponse(BaseModel):
    id: str
    tenant_id: str
    event_id: Optional[str] = None
    source: str
    hazard_code: Optional[str] = None
    description: str
    taxonomy_main: Optional[str] = None
    taxonomy_type: Optional[str] = None
    taxonomy_specific: Optional[str] = None
    unsafe_event: Optional[str] = None
    identified_hazard: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    remarks: Optional[str] = None
    csd_remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}
