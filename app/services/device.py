"""Device / organization service – delegates to DeviceRepository (PostgreSQL)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.device import DeviceRepository

logger = logging.getLogger("fsmapi.service.device")


class DeviceService:
    def __init__(self, repo: DeviceRepository):
        self._repo = repo

    async def get_devices(self, organization: Optional[str] = None) -> Any:
        return await self._repo.list_devices(organization)

    async def get_device_info(self, ip: str, organization: Optional[str] = None) -> Any:
        return await self._repo.get_device_by_ip(ip, organization)

    async def get_monitored_devices(self) -> Any:
        return await self._repo.get_monitored_devices()

    async def get_monitored_organizations(self) -> List[Dict]:
        return await self._repo.list_organizations()

    async def get_org_by_id(self, domain_id: int) -> Any:
        result = await self._repo.get_organization_by_id(domain_id)
        return result or {"message": f"Organization not found for ID {domain_id}"}
