"""Domain repository – PostgreSQL (ph_sys_domain + ph_sys_collector)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.domain")


class DomainRepository(PostgresRepository):

    async def list_domains(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                id,
                creation_time,
                cust_org_id,
                entity_version,
                last_modified_time,
                owner_id,
                disabled,
                domain_id,
                initialized,
                name,
                include_range,
                exclude_range
            FROM ph_sys_domain
            ORDER BY id
        """
        return await self.fetch(sql)

    async def list_domain_collectors(self) -> List[Dict[str, Any]]:
        """Returns all collectors with their cust_org_id (= domain_id)."""
        sql = """
            SELECT cust_org_id, natural_id
            FROM ph_sys_collector
            ORDER BY cust_org_id, id
        """
        return await self.fetch(sql)
