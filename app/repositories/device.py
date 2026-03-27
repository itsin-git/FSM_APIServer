"""
Device / organization repository – PostgreSQL.

FortiSIEM CMDB data lives in PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.device")


class DeviceRepository(PostgresRepository):

    async def list_devices(self, organization: Optional[str] = None) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <cmdb_device_table>
        #        WHERE organization = $1 (if provided)
        raise NotImplementedError("TODO: implement list_devices SQL query")

    async def get_device_by_ip(self, ip: str, organization: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <cmdb_device_table>
        #        WHERE ipAddress = $1 AND organization = $2
        raise NotImplementedError("TODO: implement get_device_by_ip SQL query")

    async def get_monitored_devices(self) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <monitored_device_table> WHERE isMonitored = true
        raise NotImplementedError("TODO: implement get_monitored_devices SQL query")

    async def list_organizations(self) -> List[Dict[str, Any]]:
        # TODO: SELECT domainId, name, ... FROM <domain_table>
        raise NotImplementedError("TODO: implement list_organizations SQL query")

    async def get_organization_by_id(self, domain_id: int) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <domain_table> WHERE domainId = $1
        raise NotImplementedError("TODO: implement get_organization_by_id SQL query")
