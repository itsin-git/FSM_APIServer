from typing import Any

from app.core.auth import require_auth
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_context_service
from app.services.context import ContextService

router = APIRouter(prefix="/context", tags=["context"], dependencies=[Depends(require_auth)])


@router.get("/ip", summary="Get IP context")
async def ip_context(
    ip: str = Query(...),
    svc: ContextService = Depends(get_context_service),
) -> Any:
    return await svc.get_ip_context({"ip": ip})


@router.get("/hostname", summary="Get hostname context")
async def host_context(
    hostname: str = Query(...),
    svc: ContextService = Depends(get_context_service),
) -> Any:
    return await svc.get_host_context({"hostname": hostname})


@router.get("/user", summary="Get user context")
async def user_context(
    user: str = Query(...),
    svc: ContextService = Depends(get_context_service),
) -> Any:
    return await svc.get_user_context({"user": user})
