"""Schemas for POST /phoenix/rest/pub/incident."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PubIncidentFilters(BaseModel):
    incidentId: Optional[List[int]] = None
    incidentStatus: Optional[List[int]] = None  # direct integer list
    status: Optional[List[int]] = None          # connector 전송 키 (incidentStatus 동일)
    eventSeverity: Optional[List[int]] = None
    eventSeverityCat: Optional[List[str]] = None
    phIncidentCategory: Optional[List[int]] = None
    phSubIncidentCategory: Optional[List[str]] = None
    phCustId: Optional[List[int]] = None
    customer: Optional[List[str]] = None
    incidentReso: Optional[List[int]] = None
    eventType: Optional[List[str]] = None       # 미지원 필드 — 수신은 하되 무시


class PubIncidentRequest(BaseModel):
    filters: Optional[PubIncidentFilters] = None
    timeFrom: Optional[int] = None
    timeTo: Optional[int] = None
    start: int = 0
    size: int = 100
    orderBy: str = "incidentLastSeen"
    descending: bool = True
    fields: Optional[List[str]] = None
