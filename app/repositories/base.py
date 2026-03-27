"""Base repository classes for PostgreSQL and ClickHouse."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import asyncpg
from clickhouse_connect.driver.asyncclient import AsyncClient


class PostgresRepository:
    """Base for repositories that query PostgreSQL via asyncpg pool."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def fetch(self, sql: str, *args: Any) -> List[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, sql: str, *args: Any) -> Optional[Dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *args)
            return dict(row) if row else None

    async def fetchval(self, sql: str, *args: Any) -> Any:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, *args)

    async def execute(self, sql: str, *args: Any) -> str:
        async with self._pool.acquire() as conn:
            return await conn.execute(sql, *args)


class ClickHouseRepository:
    """Base for repositories that query ClickHouse."""

    def __init__(self, client: AsyncClient):
        self._client = client

    async def query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        result = await self._client.query(sql, parameters=parameters or {})
        column_names = result.column_names
        return [dict(zip(column_names, row)) for row in result.result_rows]

    async def command(self, sql: str) -> None:
        await self._client.command(sql)
