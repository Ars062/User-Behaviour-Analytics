# app/schemas.py
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class AnalyticsSnapshot(BaseModel):
    metrics: Dict[str, Any]
    stats: Dict[str, Any]
    bounce_rate: float
    average_duration: float
    fetched_at: datetime

class AnalyticsResponse(BaseModel):
    website_id: str
    range: str
    snapshot: AnalyticsSnapshot
