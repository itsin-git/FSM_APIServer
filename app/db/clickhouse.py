"""
ClickHouse client manager (clickhouse-connect).

FortiSIEM stores raw event data in ClickHouse.
The event query (eventQuery / progress / result) flow
reads from ClickHouse directly.

Lifecycle:
  startup  → create_client()
  shutdown → close_client()
  request  → get_client()
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import clickhouse_connect
from clickhouse_connect.driver.asyncclient import AsyncClient

from app.core.config import Settings

logger = logging.getLogger("fsmapi.db.clickhouse")

_client: Optional[AsyncClient] = None


async def create_client(settings: Settings) -> None:
    global _client
    logger.info(
        "Connecting to ClickHouse: %s@%s:%d/%s (secure=%s)",
        settings.clickhouse_user,
        settings.clickhouse_host,
        settings.clickhouse_port,
        settings.clickhouse_db,
        settings.clickhouse_secure,
    )
    _client = await clickhouse_connect.get_async_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_db,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        secure=settings.clickhouse_secure,
    )
    logger.info("ClickHouse client created")


async def close_client() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("ClickHouse client closed")


def get_client() -> AsyncClient:
    if _client is None:
        from app.core.exceptions import FortiSIEMError
        raise FortiSIEMError(
            "ClickHouse is unavailable. Check CLICKHOUSE_HOST / CLICKHOUSE_PORT in .env",
            status_code=503,
        )
    return _client


async def execute_query(sql: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return rows as list of dicts.
    Column names are taken from query result metadata.
    """
    client = get_client()
    result = await client.query(sql, parameters=parameters or {})
    column_names = result.column_names
    return [dict(zip(column_names, row)) for row in result.result_rows]
