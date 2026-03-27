"""Redis connection singleton shared by API server and worker."""

from __future__ import annotations

import logging
from typing import Optional

from redis import Redis

logger = logging.getLogger("fsmapi.queue.redis")

_redis: Optional[Redis] = None


def get_redis() -> Redis:
    """Return the process-level Redis connection (lazy init)."""
    global _redis
    if _redis is None:
        from app.core.config import get_settings
        s = get_settings()
        _redis = Redis(
            host=s.redis_host,
            port=s.redis_port,
            db=s.redis_db,
            password=s.redis_password or None,
            decode_responses=False,  # rq requires bytes
            socket_connect_timeout=5,
            # socket_timeout 미설정: ClickHouse 쿼리가 수십 초 걸리므로
            # 짧은 timeout 설정 시 워커가 Redis 연결을 끊음
        )
        logger.info("Redis client created (%s:%s db=%s)", s.redis_host, s.redis_port, s.redis_db)
    return _redis
