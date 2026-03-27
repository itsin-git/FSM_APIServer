"""Health-check service: verifies PostgreSQL and ClickHouse connectivity."""

from __future__ import annotations

import logging
from typing import Any, Dict

import asyncpg
from clickhouse_connect.driver.asyncclient import AsyncClient

logger = logging.getLogger("fsmapi.service.health")


class HealthService:
    def __init__(self, pg_pool: asyncpg.Pool, ch_client: AsyncClient):
        self._pg = pg_pool
        self._ch = ch_client

    async def check(self) -> Dict[str, Any]:
        pg_ok, pg_msg = await self._check_postgres()
        ch_ok, ch_msg = await self._check_clickhouse()
        overall = "ok" if (pg_ok and ch_ok) else "degraded"
        return {
            "status": overall,
            "postgres": {"ok": pg_ok, "detail": pg_msg},
            "clickhouse": {"ok": ch_ok, "detail": ch_msg},
        }

    async def _check_postgres(self):
        try:
            async with self._pg.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True, "connected"
        except Exception as exc:
            logger.warning("PostgreSQL health check failed: %s", exc)
            return False, str(exc)

    async def _check_clickhouse(self):
        try:
            result = await self._ch.query("SELECT 1")
            return True, "connected"
        except Exception as exc:
            logger.warning("ClickHouse health check failed: %s", exc)
            return False, str(exc)
