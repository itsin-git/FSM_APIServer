"""Context (IP / host / user) service – delegates to ContextRepository (PostgreSQL)."""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.repositories.context import ContextRepository

logger = logging.getLogger("fsmapi.service.context")


class ContextService:
    def __init__(self, repo: ContextRepository):
        self._repo = repo

    async def get_ip_context(self, params: Dict) -> Any:
        return await self._repo.get_ip_context(params.get("ip", ""))

    async def get_host_context(self, params: Dict) -> Any:
        return await self._repo.get_host_context(params.get("hostname", ""))

    async def get_user_context(self, params: Dict) -> Any:
        return await self._repo.get_user_context(params.get("user", ""))
