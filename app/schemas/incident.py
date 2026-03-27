from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class IncidentListRequest(BaseModel):
    search: dict = Field(default_factory=dict)
    start: int = 0
    size: int = 500
    timeFrom: Optional[str] = None   # ISO-8601 e.g. "2024-01-01T00:00:00.000Z"
    timeTo: Optional[str] = None
    orderBy: Optional[str] = None    # "incidentLastSeen DESC"
    fields: Optional[List[str]] = None
    incidentStatus: Optional[List[str]] = None   # ["Active", "Auto Cleared", …]
    incidentCategory: Optional[List[str]] = None  # ["Security", "Availability", …]
    incidentSubCategory: Optional[List[str]] = None
    severity: Optional[List[str]] = None
    eventType: Optional[List[str]] = None


class IncidentDetailRequest(BaseModel):
    incidentId: Any   # int or list[int]
    timeFrom: Optional[str] = None
    timeTo: Optional[str] = None


class UpdateIncidentRequest(BaseModel):
    incidentId: int
    incidentStatus: Optional[str] = None   # "Active" | "Manually Cleared" | …
    resolution: Optional[str] = None        # "True Positive" | "False Positive"


class CommentIncidentRequest(BaseModel):
    id: int
    comment_text: str


class ClearIncidentRequest(BaseModel):
    id: int
    comment_text: str = ""


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------

class IncidentListResponse(BaseModel):
    data: List[Any]


class IncidentUpdateResponse(BaseModel):
    message: str
    incident_id: Any
