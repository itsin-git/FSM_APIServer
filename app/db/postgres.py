"""
PostgreSQL connection pool manager (asyncpg).

FortiSIEM stores incident metadata, CMDB devices, watchlists,
lookup tables, and user/organization data in PostgreSQL.

Lifecycle:
  startup  → create_pool()
  shutdown → close_pool()
  request  → get_pool() → acquire connection
"""

from __future__ import annotations

import logging
from typing import Optional

import asyncpg

from app.core.config import Settings

logger = logging.getLogger("fsmapi.db.postgres")

_pool: Optional[asyncpg.Pool] = None


async def create_pool(settings: Settings) -> None:
    global _pool
    logger.info(
        "Connecting to PostgreSQL: %s@%s:%d/%s",
        settings.postgres_user,
        settings.postgres_host,
        settings.postgres_port,
        settings.postgres_db,
    )
    _pool = await asyncpg.create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        ssl=settings.postgres_ssl,       # DSN 대신 개별 파라미터로 전달 → SSL 오동작 방지
        min_size=settings.postgres_min_pool,
        max_size=settings.postgres_max_pool,
        command_timeout=30,
        server_settings={"search_path": "public"},
    )
    logger.info("PostgreSQL pool created (min=%d, max=%d)", settings.postgres_min_pool, settings.postgres_max_pool)


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        from app.core.exceptions import FortiSIEMError
        raise FortiSIEMError(
            "PostgreSQL is unavailable. Check POSTGRES_HOST / POSTGRES_PORT / POSTGRES_PASSWORD in .env",
            status_code=503,
        )
    return _pool
