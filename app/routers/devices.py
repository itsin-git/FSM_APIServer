from typing import Any, Optional

from app.core.auth import require_auth
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_device_service
from app.services.device import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"], dependencies=[Depends(require_auth)])


@router.get("", summary="List CMDB devices")
async def list_devices(
    organization: Optional[str] = Query(None),
    svc: DeviceService = Depends(get_device_service),
) -> Any:
    return await svc.get_devices(organization)


@router.get("/monitored", summary="Get monitored devices")
async def monitored_devices(svc: DeviceService = Depends(get_device_service)) -> Any:
    return await svc.get_monitored_devices()


@router.get("/organizations", summary="Get monitored organizations")
async def monitored_organizations(svc: DeviceService = Depends(get_device_service)) -> Any:
    return await svc.get_monitored_organizations()


@router.get("/organizations/{domain_id}", summary="Get organization by ID")
async def get_org_by_id(
    domain_id: int,
    svc: DeviceService = Depends(get_device_service),
) -> Any:
    return await svc.get_org_by_id(domain_id)


@router.get("/info", summary="Get device info by IP")
async def get_device_info(
    ip: str = Query(...),
    organization: Optional[str] = Query(None),
    svc: DeviceService = Depends(get_device_service),
) -> Any:
    return await svc.get_device_info(ip, organization)
