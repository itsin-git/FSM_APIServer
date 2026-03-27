"""Watchlist service – delegates to WatchlistRepository (PostgreSQL)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.core.exceptions import FortiSIEMError
from app.repositories.watchlist import WatchlistRepository

logger = logging.getLogger("fsmapi.service.watchlist")


class WatchlistService:
    def __init__(self, repo: WatchlistRepository):
        self._repo = repo

    async def get_all(self) -> Any:
        return await self._repo.list_all()

    async def get_by_id(self, watch_list_id: int) -> Any:
        return await self._repo.get_by_id(watch_list_id)

    async def get_by_entry_id(self, entry_id: int) -> Any:
        return await self._repo.get_entry_by_id(entry_id)

    async def get_by_entry_value(self, entry_value: str) -> Any:
        return await self._repo.get_entries_by_value(entry_value)

    async def create_group(self, payload: Dict) -> Any:
        if not payload.get("displayName"):
            raise FortiSIEMError("displayName is required", status_code=422)
        if not payload.get("type"):
            raise FortiSIEMError("type is required", status_code=422)
        return await self._repo.create_group(payload)

    async def add_entries(self, watch_list_id: int, entries: List[Dict]) -> Any:
        for e in entries:
            if not e.get("entryValue"):
                raise FortiSIEMError("entryValue is required in each entry", status_code=422)
        return await self._repo.add_entries(watch_list_id, entries)

    async def delete_entries(self, entry_ids: List[int]) -> Any:
        return await self._repo.delete_entries(entry_ids)

    async def delete_watchlists(self, watchlist_ids: List[int]) -> Any:
        return await self._repo.delete_watchlists(watchlist_ids)

    async def get_entry_count(self) -> Any:
        return await self._repo.get_entry_count()
