from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
    errors: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
