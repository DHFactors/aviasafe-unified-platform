from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportPeriod(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    ANNUAL = "Annual"


class ReportType(str, Enum):
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateReportRequest(BaseModel):
    year: int = Field(..., ge=2020, le=2100)
    quarter: Optional[int] = Field(None, ge=1, le=4)


class ReportResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    report_type: ReportType
    period: str
    year: int
    quarter: Optional[int] = None
    status: ReportStatus
    summary: Dict[str, Any]
    data: Dict[str, Any]
    generated_at: datetime
    generated_by: str
    file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    report_type: ReportType
    period: str
    year: int
    quarter: Optional[int] = None
    status: ReportStatus
    generated_at: Optional[datetime] = None
    generated_by: Optional[str] = None
    file_url: Optional[str] = None
