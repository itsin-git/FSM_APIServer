"""
Lookup table repository – PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.base import PostgresRepository

logger = logging.getLogger("fsmapi.repo.lookup_table")


class LookupTableRepository(PostgresRepository):

    async def list_tables(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <lookup_table_meta> WHERE ...filters...
        raise NotImplementedError("TODO: implement list_tables SQL query")

    async def create_table(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: INSERT INTO <lookup_table_meta> (...) VALUES (...) RETURNING *
        raise NotImplementedError("TODO: implement create_table SQL query")

    async def delete_table(self, lookup_table_id: str) -> bool:
        # TODO: DELETE FROM <lookup_table_meta> WHERE id = $1
        raise NotImplementedError("TODO: implement delete_table SQL query")

    async def get_table_data(
        self,
        lookup_table_id: str,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        # TODO: SELECT * FROM <lookup_table_data> WHERE tableId = $1
        raise NotImplementedError("TODO: implement get_table_data SQL query")

    async def update_table_data(
        self, lookup_table_id: str, key: str, column_data: Any
    ) -> bool:
        # TODO: UPDATE <lookup_table_data> SET columnData = $3
        #        WHERE tableId = $1 AND key = $2
        raise NotImplementedError("TODO: implement update_table_data SQL query")

    async def delete_table_data(self, lookup_table_id: str, keys: List[str]) -> bool:
        # TODO: DELETE FROM <lookup_table_data>
        #        WHERE tableId = $1 AND key = ANY($2)
        raise NotImplementedError("TODO: implement delete_table_data SQL query")

    async def check_import_status(self, lookup_table_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        # TODO: SELECT * FROM <import_task_table>
        #        WHERE tableId = $1 AND taskId = $2
        raise NotImplementedError("TODO: implement check_import_status SQL query")
