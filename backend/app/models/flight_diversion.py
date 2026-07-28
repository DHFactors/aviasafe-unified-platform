from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DiversionReason(str, Enum):
    WEATHER = "Weather"
    TECHNICAL = "Technical"
    MEDICAL = "Medical"
    FUEL = "Fuel"
    SECURITY = "Security"
    OPERATIONAL = "Operational"
    AIRPORT_CLOSURE = "Airport Closure"
    AIR_TRAFFIC_CONTROL = "Air Traffic Control"
    OTHER = "Other"


class DiversionStatus(str, Enum):
    PENDING = "Pending"
    REVIEWED = "Reviewed"
    INVESTIGATING = "Investigating"
    CLOSED = "Closed"
    LINKED_TO_HAZARD = "Linked to Hazard"


class FlightDiversionCreate(BaseModel):
    date: datetime = Field(...)
    flight_number: str = Field(..., min_length=2, max_length=20)
    aircraft_registration: str = Field(..., min_length=3, max_length=10)
    sector_from: str = Field(..., min_length=2, max_length=10)
    sector_to: str = Field(..., min_length=2, max_length=10)
    diverted_to: str = Field(..., min_length=2, max_length=10)
    reason: DiversionReason = Field(...)
    reason_details: Optional[str] = None
    captain: Optional[str] = None
    first_officer: Optional[str] = None
    air_hostess: Optional[str] = None
    description: str = Field(..., min_length=10)
    additional_fuel_cost: Optional[float] = None
    passenger_impact: Optional[int] = None
    delay_minutes: Optional[int] = None
    remarks: Optional[str] = None


class FlightDiversionUpdate(BaseModel):
    date: Optional[datetime] = None
    flight_number: Optional[str] = None
    aircraft_registration: Optional[str] = None
    sector_from: Optional[str] = None
    sector_to: Optional[str] = None
    diverted_to: Optional[str] = None
    reason: Optional[DiversionReason] = None
    reason_details: Optional[str] = None
    captain: Optional[str] = None
    first_officer: Optional[str] = None
    air_hostess: Optional[str] = None
    description: Optional[str] = None
    additional_fuel_cost: Optional[float] = None
    passenger_impact: Optional[int] = None
    delay_minutes: Optional[int] = None
    remarks: Optional[str] = None
    status: Optional[DiversionStatus] = None


class FlightDiversionResponse(BaseModel):
    id: str
    tenant_id: str
    diversion_id: str
    date: datetime
    flight_number: str
    aircraft_registration: str
    sector_from: str
    sector_to: str
    diverted_to: str
    reason: DiversionReason
    reason_details: Optional[str] = None
    captain: Optional[str] = None
    first_officer: Optional[str] = None
    air_hostess: Optional[str] = None
    description: str
    additional_fuel_cost: Optional[float] = None
    passenger_impact: Optional[int] = None
    delay_minutes: Optional[int] = None
    remarks: Optional[str] = None
    status: DiversionStatus
    hazard_id: Optional[str] = None
    hazard_link_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}


class DiversionStats(BaseModel):
    total_diversions: int = 0
    by_reason: Dict[str, int]
    by_airport: Dict[str, int]
    by_aircraft: Dict[str, int]
    by_month: List[Dict[str, Any]]
    weather_diversion_rate: float = 0.0
    technical_diversion_rate: float = 0.0
    avg_delay_minutes: int = 0
    total_fuel_cost_impact: float = 0.0
    total_passenger_impact: int = 0
