from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventQueryRequest(BaseModel):
    xml_payload: Optional[str] = None
    sql_query: Optional[str] = None
    select_clause: str = ""
    conditions: str = ""
    groupby: str = ""
    orderby: str = ""
    attr_list: str = ""
    rel_time: Optional[str] = None   # "Minutes" | "Hours" | "Days"
    value: int = 0
    time_from: Optional[str] = None  # ISO-8601
    time_to: Optional[str] = None


class EventQueryResponse(BaseModel):
    query_id: str


class EventProgressResponse(BaseModel):
    query_id: str
    progress_pct: Any


class EventResultRequest(BaseModel):
    start: int = 0
    per_page: int = 50


class EventResultResponse(BaseModel):
    query_id: Optional[str] = Field(None, alias="queryId")
    total_count: Optional[Any] = Field(None, alias="totalCount")
    events: List[Any] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class AssociatedEventsRequest(BaseModel):
    incident_id: int
    per_page: int = 10
    timeFrom: Optional[str] = None
    timeTo: Optional[str] = None


class SearchEventsRequest(BaseModel):
    query_string: str
    select_clause: str = ""
    rel_time: Optional[str] = None
    value: int = 0
    time_from: Optional[str] = None
    time_to: Optional[str] = None
    start: int = 0
    per_page: int = 50
