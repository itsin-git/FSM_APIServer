"""Lookup-table service – delegates to LookupTableRepository (PostgreSQL)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.lookup_table import LookupTableRepository

logger = logging.getLogger("fsmapi.service.lookup_table")


class LookupTableService:
    def __init__(self, repo: LookupTableRepository):
        self._repo = repo

    async def list_tables(self, params: Optional[Dict] = None) -> Any:
        return await self._repo.list_tables(params)

    async def create_table(self, payload: Dict) -> Any:
        return await self._repo.create_table(payload)

    async def delete_table(self, lookup_table_id: str) -> Dict[str, str]:
        await self._repo.delete_table(lookup_table_id)
        return {"message": "Lookup table deleted successfully", "status": "Success"}

    async def get_table_data(self, lookup_table_id: str, extra_params: Optional[Dict] = None) -> Any:
        return await self._repo.get_table_data(lookup_table_id, extra_params)

    async def update_table_data(self, lookup_table_id: str, key: str, column_data: Any) -> Dict[str, Any]:
        await self._repo.update_table_data(lookup_table_id, key, column_data)
        return {"message": "Lookup table updated successfully"}

    async def delete_table_data(self, lookup_table_id: str, keys_data: List) -> Dict[str, str]:
        await self._repo.delete_table_data(lookup_table_id, keys_data)
        return {"message": "Input keys data deleted successfully", "status": "Success"}

    async def check_import_status(self, lookup_table_id: str, task_id: str) -> Any:
        return await self._repo.check_import_status(lookup_table_id, task_id)
