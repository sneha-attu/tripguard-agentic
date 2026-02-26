from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RebookRequest(BaseModel):
    booking_id: str
    user_id: str  # employee_id
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    airline: str
    disruption_type: Optional[str] = "auto"


class AlternativeFlight(BaseModel):
    flight_number: str
    airline: str
    departure_time: str
    arrival_time: str
    price: float


class RebookResponse(BaseModel):
    booking_id: str
    disruption_detected: bool
    disruption_type: Optional[str]
    policy_compliant: bool
    recommended_flight: Optional[AlternativeFlight]
    alternatives: Optional[List[AlternativeFlight]]
    ai_confidence: float
    ai_reasoning: str
    message: str