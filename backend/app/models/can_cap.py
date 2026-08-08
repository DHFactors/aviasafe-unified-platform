from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CANStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    CLOSED = "Closed"
    ESCALATED = "Escalated"


class CAPStatus(str, Enum):
    IN_PROGRESS = "In Progress"
    UNDER_REVIEW = "Under Review"
    COMPLETED = "Completed"
    REVISION_REQUIRED = "Revision Required"
    OVERDUE = "Overdue"


class CANPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ─── CAN ───

class CANCreate(BaseModel):
    hazard_id: str = Field(...)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    required_action: str = Field(...)
    target_completion_date: datetime = Field(...)
    assigned_to: str = Field(...)
    assigned_to_uid: str = Field(...)
    department: Optional[str] = None
    priority: str = Field(..., pattern="^(High|Medium|Low)$")


class CANUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    required_action: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[CANStatus] = None


class CANResponse(BaseModel):
    id: str
    can_reference: str
    hazard_id: str
    title: str
    description: str
    required_action: str
    issued_by: str
    issued_by_uid: str
    issued_at: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    assigned_to: str
    assigned_to_uid: str
    department: Optional[str] = None
    priority: str
    status: str
    tenant_id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    latest_cap: Optional[dict] = None

    model_config = {"from_attributes": True}


class CANListItem(BaseModel):
    id: str
    can_reference: str
    hazard_id: str
    title: str
    priority: str
    status: str
    assigned_to: str
    target_completion_date: Optional[datetime] = None
    issued_at: Optional[datetime] = None


# ─── CAP ───

class CAPCreate(BaseModel):
    can_id: str = Field(...)
    action_plan: str = Field(..., min_length=10)
    timeline: str = Field(...)
    resources_required: Optional[str] = None
    implementation_plan: Optional[str] = None
    department: Optional[str] = None
    target_completion_date: datetime = Field(...)


class CAPUpdate(BaseModel):
    status: Optional[CAPStatus] = None
    action_plan: Optional[str] = None
    timeline: Optional[str] = None
    resources_required: Optional[str] = None
    implementation_plan: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    review_comments: Optional[str] = None


class CAPReview(BaseModel):
    status: CAPStatus
    comments: Optional[str] = None
    revision_deadline: Optional[datetime] = None


class CAPResponse(BaseModel):
    id: str
    can_id: str
    cap_reference: str
    action_plan: str
    timeline: str
    resources_required: Optional[str] = None
    implementation_plan: Optional[str] = None
    submitted_by: str
    submitted_by_uid: str
    department: Optional[str] = None
    submitted_at: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    status: str
    reviewed_by: Optional[str] = None
    reviewed_by_uid: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    revision_deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
