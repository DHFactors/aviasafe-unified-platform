from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CAPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CAStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    UNDER_REVIEW = "Under Review"
    COMPLETED = "Completed"
    CLOSED = "Closed"


class CorrectiveActionCreate(BaseModel):
    tenant_id: str = Field(...)
    hazard_id: Optional[str] = None
    can_id: Optional[str] = None
    event_id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    action_plan: str = Field(...)
    priority: CAPriority = CAPriority.MEDIUM
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    status: CAStatus = CAStatus.OPEN
    remarks: Optional[str] = None


class CorrectiveActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    action_plan: Optional[str] = None
    priority: Optional[CAPriority] = None
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    status: Optional[CAStatus] = None
    remarks: Optional[str] = None


class CorrectiveActionResponse(BaseModel):
    id: str
    tenant_id: str
    hazard_id: Optional[str] = None
    can_id: Optional[str] = None
    event_id: Optional[str] = None
    title: str
    description: str
    action_plan: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_to_uid: Optional[str] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}
