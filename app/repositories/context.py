"""
Context (IP / host / user) repository – PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.context")


class ContextRepository(PostgresRepository):

    async def get_ip_context(self, ip: str) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <context_ip_table> WHERE ipAddress = $1
        raise NotImplementedError("TODO: implement get_ip_context SQL query")

    async def get_host_context(self, hostname: str) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <context_host_table> WHERE hostname = $1
        raise NotImplementedError("TODO: implement get_host_context SQL query")

    async def get_user_context(self, user: str) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <context_user_table> WHERE username = $1
        raise NotImplementedError("TODO: implement get_user_context SQL query")
