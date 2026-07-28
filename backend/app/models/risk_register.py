from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RiskTolerability(str, Enum):
    ACCEPTABLE = "Acceptable"
    TOLERABLE = "Tolerable"
    INTOLERABLE = "Intolerable"


class RiskRegisterStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "Under Review"
    CLOSED = "closed"


class RiskRegisterCreate(BaseModel):
    tenant_id: str = Field(...)
    hazard_id: str = Field(...)
    srm_date: datetime = Field(...)
    ultimate_consequence: str = Field(..., min_length=10)
    existing_severity: Optional[int] = Field(None, ge=1, le=5)
    existing_probability: Optional[int] = Field(None, ge=1, le=5)
    existing_risk_index: Optional[int] = None
    existing_risk_tolerability: Optional[str] = None
    resultant_severity: Optional[int] = Field(None, ge=1, le=5)
    resultant_probability: Optional[int] = Field(None, ge=1, le=5)
    resultant_risk_index: Optional[int] = None
    resultant_risk_tolerability: Optional[str] = None
    status: RiskRegisterStatus = RiskRegisterStatus.OPEN
    follow_up_date: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    remarks: Optional[str] = None
    concerned_department: Optional[str] = None


class RiskRegisterUpdate(BaseModel):
    srm_date: Optional[datetime] = None
    ultimate_consequence: Optional[str] = None
    existing_severity: Optional[int] = None
    existing_probability: Optional[int] = None
    existing_risk_index: Optional[int] = None
    existing_risk_tolerability: Optional[str] = None
    resultant_severity: Optional[int] = None
    resultant_probability: Optional[int] = None
    resultant_risk_index: Optional[int] = None
    resultant_risk_tolerability: Optional[str] = None
    status: Optional[RiskRegisterStatus] = None
    follow_up_date: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    remarks: Optional[str] = None
    concerned_department: Optional[str] = None


class RiskRegisterResponse(BaseModel):
    id: str
    tenant_id: str
    hazard_id: str
    srm_date: Optional[datetime] = None
    ultimate_consequence: str
    existing_severity: Optional[int] = None
    existing_probability: Optional[int] = None
    existing_risk_index: Optional[int] = None
    existing_risk_tolerability: Optional[str] = None
    resultant_severity: Optional[int] = None
    resultant_probability: Optional[int] = None
    resultant_risk_index: Optional[int] = None
    resultant_risk_tolerability: Optional[str] = None
    status: str
    follow_up_date: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    remarks: Optional[str] = None
    concerned_department: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}
