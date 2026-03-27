from typing import Any, Optional

from app.core.auth import require_auth
from fastapi import APIRouter, Depends

from app.dependencies import get_incident_service
from app.schemas.incident import (
    ClearIncidentRequest,
    CommentIncidentRequest,
    IncidentDetailRequest,
    IncidentListRequest,
    IncidentListResponse,
    IncidentUpdateResponse,
    UpdateIncidentRequest,
)
from app.services.incident import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"], dependencies=[Depends(require_auth)])


@router.post("", response_model=IncidentListResponse, summary="List incidents")
async def list_incidents(
    req: IncidentListRequest,
    svc: IncidentService = Depends(get_incident_service),
):
    return await svc.list_incidents(req)


@router.post("/detail", summary="Get incident details")
async def get_incident_detail(
    req: IncidentDetailRequest,
    svc: IncidentService = Depends(get_incident_service),
) -> Any:
    return await svc.get_detail(req)


@router.put("", response_model=IncidentUpdateResponse, summary="Update incident")
async def update_incident(
    req: UpdateIncidentRequest,
    svc: IncidentService = Depends(get_incident_service),
):
    return await svc.update(req)


@router.post("/comment", response_model=IncidentUpdateResponse, summary="Add comment to incident")
async def comment_incident(
    req: CommentIncidentRequest,
    svc: IncidentService = Depends(get_incident_service),
):
    return await svc.comment(req)


@router.post("/clear", response_model=IncidentUpdateResponse, summary="Clear incident")
async def clear_incident(
    req: ClearIncidentRequest,
    svc: IncidentService = Depends(get_incident_service),
):
    return await svc.clear(req)


@router.get("/{incident_id}/events", summary="Get associated triggering events")
async def get_associated_events(
    incident_id: int,
    per_page: int = 10,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    svc: IncidentService = Depends(get_incident_service),
) -> Any:
    return await svc.get_associated_events(incident_id, per_page, time_from, time_to)
