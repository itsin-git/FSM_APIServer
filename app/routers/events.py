"""
Event query router.

URL paths match the FortiSIEM 7.4.2 OpenAPI spec exactly:
  POST /phoenix/rest/query/eventQuery
  POST /phoenix/rest/query/archive
  GET  /phoenix/rest/query/progress/{queryId}
  GET  /phoenix/rest/query/events/{queryId}/{offset}/{limit}

Request body:
  - Content-Type: text/xml  → raw XML string (FortiSOAR connector 방식)
  - Content-Type: application/json → EventQueryRequest JSON (직접 호출 방식)
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Request

from app.core.auth import require_auth
from app.dependencies import get_event_service
from app.schemas.event import (
    EventProgressResponse,
    EventQueryRequest,
    EventQueryResponse,
    EventResultResponse,
    SearchEventsRequest,
)
from app.services.event import EventService

router = APIRouter(
    prefix="/phoenix/rest/query",
    tags=["Event Query"],
    dependencies=[Depends(require_auth)],
)


async def _parse_query_request(request: Request) -> EventQueryRequest:
    """
    Content-Type에 따라 요청을 파싱한다.
    - text/xml  : raw XML을 xml_payload로 감싼다 (FortiSOAR connector 호환)
    - 그 외      : JSON body를 EventQueryRequest로 파싱한다
    """
    ct = request.headers.get("content-type", "")
    if "xml" in ct:
        body = await request.body()
        return EventQueryRequest(xml_payload=body.decode("utf-8", errors="replace"))
    data = await request.json()
    return EventQueryRequest(**data)


@router.post(
    "/eventQuery",
    response_model=EventQueryResponse,
    summary="Submit FortiSIEM XML Report query against online storage",
)
async def submit_event_query(
    request: Request,
    svc: EventService = Depends(get_event_service),
):
    req = await _parse_query_request(request)
    query_id = await svc.submit_query(req)
    return {"query_id": query_id}


@router.post(
    "/archive",
    response_model=EventQueryResponse,
    summary="Submit FortiSIEM XML Report query against archive storage",
)
async def submit_archive_query(
    request: Request,
    svc: EventService = Depends(get_event_service),
):
    # TODO: archive 쿼리는 별도 ClickHouse 파티션/테이블 대상
    req = await _parse_query_request(request)
    query_id = await svc.submit_query(req)
    return {"query_id": query_id}


@router.get(
    "/progress/{queryId}",
    response_model=EventProgressResponse,
    summary="Get FortiSIEM Query Progress",
)
async def get_query_progress(
    queryId: str = Path(..., description="Query ID returned by eventQuery or archive"),
    svc: EventService = Depends(get_event_service),
):
    return await svc.get_progress(queryId)


@router.get(
    "/events/{queryId}/{offset}/{limit}",
    response_model=EventResultResponse,
    response_model_by_alias=False,
    summary="Get Query Results from either an online or archive storage query",
)
async def get_query_events(
    queryId: str = Path(...),
    offset: int = Path(..., ge=0),
    limit: int = Path(..., ge=1, le=10000),
    svc: EventService = Depends(get_event_service),
):
    return await svc.get_results(queryId, offset, limit)


# ------------------------------------------------------------------
# 편의 엔드포인트 (스펙 외)
# ------------------------------------------------------------------

@router.post("/search", summary="[Extra] One-shot event search")
async def search_events(
    req: SearchEventsRequest,
    svc: EventService = Depends(get_event_service),
) -> Any:
    return await svc.search_events(req)


@router.get("/by-id/{eventId}", summary="[Extra] Get single event by ID")
async def get_event_by_id(
    eventId: str = Path(...),
    select_clause: str = "",
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    svc: EventService = Depends(get_event_service),
) -> Any:
    return await svc.get_event_by_id(eventId, select_clause, time_from, time_to)
