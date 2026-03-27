"""
Public incident endpoints.

GET  /phoenix/rest/pub/incident                              — query by time range (query params)
POST /phoenix/rest/pub/incident                              — query with filters, ordering, pagination (JSON body)
GET  /phoenix/rest/pub/incident/triggeringEvents/start      — start triggering-events query, returns queryId
GET  /phoenix/rest/pub/incident/triggeringEvents/progress/{queryId}  — always returns progressPct=100
GET  /phoenix/rest/pub/incident/triggeringEvents/result/{queryId}    — returns cached event list
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query

from app.core.auth import require_auth
from app.dependencies import get_incident_service, get_triggering_events_service
from app.schemas.pub_incident import PubIncidentRequest
from app.services.incident import IncidentService, TriggeringEventsService

router = APIRouter(prefix="/phoenix/rest/pub", tags=["pub-incidents"])


@router.get("/incident", summary="List incidents by time range")
async def list_pub_incidents_get(
    timeFrom: Optional[int] = Query(None, description="Start of time range (epoch ms)"),
    timeTo: Optional[int] = Query(None, description="End of time range (epoch ms)"),
    size: int = Query(100, ge=1, le=10000),
    start: int = Query(0, ge=0),
    orderBy: str = Query("incidentLastSeen"),
    descending: bool = Query(True),
    _auth: str = Depends(require_auth),
    svc: IncidentService = Depends(get_incident_service),
) -> Dict[str, Any]:
    return await svc.list_pub_incidents(
        time_from_ms=timeFrom,
        time_to_ms=timeTo,
        size=size,
        start=start,
        order_by=orderBy,
        descending=descending,
    )


@router.post("/incident", summary="List incidents with filters")
async def list_pub_incidents_post(
    req: PubIncidentRequest,
    _auth: str = Depends(require_auth),
    svc: IncidentService = Depends(get_incident_service),
) -> Dict[str, Any]:
    filters = req.filters.model_dump(exclude_none=True) if req.filters else None
    return await svc.list_pub_incidents(
        time_from_ms=req.timeFrom,
        time_to_ms=req.timeTo,
        size=req.size,
        start=req.start,
        filters=filters,
        order_by=req.orderBy,
        descending=req.descending,
    )


# ------------------------------------------------------------------
# Triggering events — 3-step async simulation
# ------------------------------------------------------------------

@router.get(
    "/incident/triggeringEvents/start",
    summary="Start triggering-events query for an incident",
)
async def triggering_events_start(
    incidentId: int = Query(..., description="Incident ID"),
    size: int = Query(100, ge=1, le=10000, description="Max number of events to return"),
    timeFrom: Optional[int] = Query(None, description="Start of time range (epoch ms)"),
    timeTo: Optional[int] = Query(None, description="End of time range (epoch ms)"),
    _auth: str = Depends(require_auth),
    svc: TriggeringEventsService = Depends(get_triggering_events_service),
) -> Dict[str, Any]:
    query_id = await svc.start_query(incidentId, size)
    return {"queryId": query_id}


@router.get(
    "/incident/triggeringEvents/progress/{queryId}",
    summary="Get triggering-events query progress",
)
async def triggering_events_progress(
    queryId: str = Path(...),
    _auth: str = Depends(require_auth),
    svc: TriggeringEventsService = Depends(get_triggering_events_service),
) -> Dict[str, Any]:
    return svc.get_progress(queryId)


@router.get(
    "/incident/triggeringEvents/result/{queryId}",
    summary="Get triggering-events query result",
)
async def triggering_events_result(
    queryId: str = Path(...),
    _auth: str = Depends(require_auth),
    svc: TriggeringEventsService = Depends(get_triggering_events_service),
) -> Dict[str, Any]:
    return svc.get_result(queryId)
