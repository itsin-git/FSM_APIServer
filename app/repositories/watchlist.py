"""
Watchlist repository – PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.watchlist")


class WatchlistRepository(PostgresRepository):

    async def list_all(self) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <watchlist_table>
        raise NotImplementedError("TODO: implement list_all SQL query")

    async def get_by_id(self, watch_list_id: int) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <watchlist_table> WHERE id = $1
        raise NotImplementedError("TODO: implement get_by_id SQL query")

    async def get_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <watchlist_entry_table> WHERE id = $1
        raise NotImplementedError("TODO: implement get_entry_by_id SQL query")

    async def get_entries_by_value(self, entry_value: str) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <watchlist_entry_table> WHERE entryValue = $1
        raise NotImplementedError("TODO: implement get_entries_by_value SQL query")

    async def create_group(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: INSERT INTO <watchlist_table> (displayName, type, ...)
        #        VALUES ($1, $2, ...) RETURNING *
        raise NotImplementedError("TODO: implement create_group SQL query")

    async def add_entries(self, watch_list_id: int, entries: List[Dict[str, Any]]) -> bool:
        # TODO: INSERT INTO <watchlist_entry_table> (watchlistId, entryValue, ...)
        #        VALUES ($1, $2, ...)
        raise NotImplementedError("TODO: implement add_entries SQL query")

    async def delete_entries(self, entry_ids: List[int]) -> bool:
        # TODO: DELETE FROM <watchlist_entry_table> WHERE id = ANY($1)
        raise NotImplementedError("TODO: implement delete_entries SQL query")

    async def delete_watchlists(self, watchlist_ids: List[int]) -> bool:
        # TODO: DELETE FROM <watchlist_table> WHERE id = ANY($1)
        raise NotImplementedError("TODO: implement delete_watchlists SQL query")

    async def get_entry_count(self) -> int:
        # TODO: SELECT count(*) FROM <watchlist_entry_table>
        raise NotImplementedError("TODO: implement get_entry_count SQL query")
