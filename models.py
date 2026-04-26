from pydantic import BaseModel
from typing import Optional


class TriageRequest(BaseModel):
    message: str
    sender_name: Optional[str] = "Unknown"
    sender_email: Optional[str] = ""


class ExtractedEntities(BaseModel):
    farmer_id: Optional[str] = None
    crop_type: Optional[str] = None
    location: Optional[str] = None
    dates: list[str] = []
    issue_keywords: list[str] = []


class TriageResponse(BaseModel):
    urgency: str           # HIGH / MEDIUM / LOW
    urgency_score: int     # 1-10
    intent: str            # e.g. "Pest Report", "Irrigation Issue", etc.
    entities: ExtractedEntities
    draft_response: str
    summary: str
    processing_time_ms: int
